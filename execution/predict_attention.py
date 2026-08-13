#!/usr/bin/env python3
"""
Attention Prediction Engine — Design Agency

Produces synthetic saliency heatmaps and Area-Of-Interest (AOI) scores for any
UI screenshot, so the heatmap_analyst skill can verify that the brand's intended
focal points (hero CTA, logo, headline, trust signals) are actually winning
predicted attention before the deliverable is shipped.

Predictor fallback chain (best available wins):

    1. UEyes (CHI 2023)            — UI-trained saliency, highest fit
       Activated when execution/.models/ueyes/ contains pretrained weights.
       https://github.com/YueJiang-nj/UEyes-CHI2023

    2. DeepGaze IIE                 — General-purpose academic baseline
       Activated when `deepgaze_pytorch` is importable.
       pip install deepgaze-pytorch

    3. OpenCV spectral / fine-grain — Always available, lower fidelity
       Pure OpenCV, no ML deps. Used as the floor.

Hardware:
    - Apple Silicon (MPS) if available, else CUDA, else CPU.
    - Runtime per 1440x900 screenshot: ~3s on M-series, ~10-20s on CPU.

Usage:
    python predict_attention.py --screenshot path/to/landing_desktop.png \\
                                --out ./assets/heatmaps/ \\
                                --label landing_page_desktop

Output files (written to --out):
    <label>_heatmap.png   Saliency overlay (jet colormap @ 0.55 alpha) on original
    <label>_saliency.png  Raw grayscale saliency map (debug)
    <label>_aoi.json      Top-N attention zones with bbox + integrated score
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Predictor interface
# ---------------------------------------------------------------------------


class SaliencyPredictor:
    """Base interface every predictor implements."""

    name = "base"

    def predict(self, image_rgb: np.ndarray) -> np.ndarray:
        """Return a float32 saliency map in [0, 1], shape matches input HxW."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1. UEyes predictor (CHI 2023, UI-trained)
# ---------------------------------------------------------------------------


class UEyesPredictor(SaliencyPredictor):
    name = "ueyes"

    def __init__(self, weights_dir: Path):
        import torch  # noqa: F401  (presence checked here, used by UEyes)

        self.weights_dir = weights_dir
        # UEyes ships its own model loader; we late-import so the optional
        # dep doesn't crash the script when the user hasn't installed it.
        sys.path.insert(0, str(weights_dir))
        try:
            from ueyes_model import load_pretrained  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                f"UEyes weights present at {weights_dir} but ueyes_model.py "
                f"not importable: {exc}"
            ) from exc
        self.model = load_pretrained(weights_dir)

    def predict(self, image_rgb: np.ndarray) -> np.ndarray:
        import torch

        device = _torch_device()
        tensor = torch.from_numpy(image_rgb).permute(2, 0, 1).float().unsqueeze(0) / 255.0
        tensor = tensor.to(device)
        with torch.no_grad():
            sal = self.model(tensor).squeeze().cpu().numpy()
        sal = sal.astype(np.float32)
        return _normalize(sal)


# ---------------------------------------------------------------------------
# 2. DeepGaze IIE predictor (general-purpose, pip-installable)
# ---------------------------------------------------------------------------


class DeepGazePredictor(SaliencyPredictor):
    name = "deepgaze-iie"

    def __init__(self):
        import torch
        from deepgaze_pytorch import DeepGazeIIE  # type: ignore

        device = _torch_device()
        self.device = device
        self.model = DeepGazeIIE(pretrained=True).to(device).eval()
        # Centerbias prior — uniform if we don't have a learned one;
        # DeepGaze expects a log-density centerbias of matching HxW per image.
        self._cb_cache: dict[tuple[int, int], "torch.Tensor"] = {}

    def _centerbias(self, h: int, w: int):
        import torch

        key = (h, w)
        if key not in self._cb_cache:
            cb = np.zeros((h, w), dtype=np.float32)
            self._cb_cache[key] = torch.from_numpy(cb).unsqueeze(0).to(self.device)
        return self._cb_cache[key]

    def predict(self, image_rgb: np.ndarray) -> np.ndarray:
        import torch

        h, w = image_rgb.shape[:2]
        tensor = (
            torch.from_numpy(image_rgb).permute(2, 0, 1).float().unsqueeze(0).to(self.device)
        )
        cb = self._centerbias(h, w)
        with torch.no_grad():
            log_density = self.model(tensor, cb)
        sal = log_density.squeeze().cpu().numpy()
        sal = np.exp(sal - sal.max())  # back to density
        return _normalize(sal.astype(np.float32))


# ---------------------------------------------------------------------------
# 3. OpenCV spectral / fine-grained saliency (always available floor)
# ---------------------------------------------------------------------------


class OpenCVSaliencyPredictor(SaliencyPredictor):
    name = "opencv-finegrained"

    def __init__(self):
        import cv2  # noqa: F401

    def predict(self, image_rgb: np.ndarray) -> np.ndarray:
        import cv2

        bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        sal_obj = cv2.saliency.StaticSaliencyFineGrained_create()
        ok, sal = sal_obj.computeSaliency(bgr)
        if not ok:
            sal_obj = cv2.saliency.StaticSaliencySpectralResidual_create()
            ok, sal = sal_obj.computeSaliency(bgr)
        if not ok:
            raise RuntimeError("OpenCV saliency failed on both fine-grained and spectral.")
        sal = sal.astype(np.float32)
        # Mild center bias to mimic real fixation behavior — pure OpenCV
        # saliency is contrast-driven only, while users actually anchor center.
        sal = _apply_center_bias(sal, weight=0.25)
        return _normalize(sal)


# ---------------------------------------------------------------------------
# Predictor selection
# ---------------------------------------------------------------------------


def select_predictor(prefer: str = "auto", model_dir: Path | None = None) -> SaliencyPredictor:
    """Pick the best available predictor."""
    candidates: list[str]
    if prefer == "auto":
        candidates = ["ueyes", "deepgaze", "opencv"]
    else:
        candidates = [prefer]

    errors: list[str] = []
    for name in candidates:
        try:
            if name == "ueyes":
                weights = model_dir or (Path(__file__).parent / ".models" / "ueyes")
                if not weights.exists():
                    raise FileNotFoundError(f"UEyes weights not found at {weights}")
                return UEyesPredictor(weights)
            if name == "deepgaze":
                return DeepGazePredictor()
            if name == "opencv":
                return OpenCVSaliencyPredictor()
            raise ValueError(f"Unknown predictor: {name}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"  - {name}: {exc}")
            continue

    raise RuntimeError(
        "No saliency predictor could be initialized. Tried:\n" + "\n".join(errors)
    )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _torch_device():
    import torch

    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _normalize(sal: np.ndarray) -> np.ndarray:
    sal = sal - sal.min()
    peak = sal.max()
    if peak <= 0:
        return np.zeros_like(sal, dtype=np.float32)
    return (sal / peak).astype(np.float32)


def _apply_center_bias(sal: np.ndarray, weight: float = 0.25) -> np.ndarray:
    h, w = sal.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    dist = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2)
    center = np.clip(1.0 - dist, 0.0, 1.0)
    return sal * (1.0 - weight) + center * weight * sal.max()


def load_image(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def save_overlay(image_rgb: np.ndarray, saliency: np.ndarray, out_path: Path, alpha: float = 0.55):
    """Render a jet-colormap heatmap blended over the original."""
    import cv2

    sal8 = (saliency * 255.0).clip(0, 255).astype(np.uint8)
    heat_bgr = cv2.applyColorMap(sal8, cv2.COLORMAP_JET)
    heat_rgb = cv2.cvtColor(heat_bgr, cv2.COLOR_BGR2RGB)
    blended = (image_rgb.astype(np.float32) * (1.0 - alpha) + heat_rgb.astype(np.float32) * alpha)
    blended = blended.clip(0, 255).astype(np.uint8)
    Image.fromarray(blended).save(out_path)


def save_grayscale(saliency: np.ndarray, out_path: Path):
    sal8 = (saliency * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(sal8, mode="L").save(out_path)


def extract_aois(saliency: np.ndarray, top_n: int = 5, threshold_pct: float = 80.0) -> list[dict]:
    """
    Extract the top-N Areas Of Interest from the saliency map.
    Returns list of {rank, bbox: [x, y, w, h], score, center: [cx, cy], coverage}.
    """
    import cv2

    h, w = saliency.shape
    thresh_value = np.percentile(saliency, threshold_pct)
    mask = (saliency >= thresh_value).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    aois: list[dict] = []
    total_saliency = float(saliency.sum())
    if total_saliency <= 0:
        return aois

    for lbl in range(1, num_labels):
        x, y, bw, bh, area = stats[lbl]
        if area < (h * w) * 0.001:  # skip tiny noise blobs (<0.1% area)
            continue
        region = saliency[y : y + bh, x : x + bw]
        region_mask = labels[y : y + bh, x : x + bw] == lbl
        integrated = float(region[region_mask].sum())
        peak = float(region[region_mask].max())
        cy = y + bh / 2.0
        cx = x + bw / 2.0
        aois.append(
            {
                "bbox": [int(x), int(y), int(bw), int(bh)],
                "center": [float(round(cx, 1)), float(round(cy, 1))],
                "center_normalized": [
                    float(round(cx / w, 3)),
                    float(round(cy / h, 3)),
                ],
                "area_px": int(area),
                "coverage": float(round(area / (h * w), 4)),
                "score_integrated": round(integrated, 2),
                "score_peak": round(peak, 4),
                "share_of_attention": round(integrated / total_saliency, 4),
            }
        )

    aois.sort(key=lambda a: a["score_integrated"], reverse=True)
    aois = aois[:top_n]
    for rank, aoi in enumerate(aois, start=1):
        aoi["rank"] = rank
        aoi["zone"] = _classify_zone(aoi["center_normalized"])
    return aois


def _classify_zone(center_norm: list[float]) -> str:
    """Map a normalized center to a 3x3 page zone (above-fold-left, etc.)."""
    cx, cy = center_norm
    col = "left" if cx < 0.34 else ("center" if cx < 0.67 else "right")
    row = "top" if cy < 0.34 else ("mid" if cy < 0.67 else "bottom")
    return f"{row}-{col}"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run(
    screenshot: Path,
    out_dir: Path,
    label: str,
    prefer: str = "auto",
    top_n: int = 5,
) -> dict:
    if not screenshot.exists():
        raise FileNotFoundError(f"Screenshot not found: {screenshot}")
    out_dir.mkdir(parents=True, exist_ok=True)

    image_rgb = load_image(screenshot)
    h, w = image_rgb.shape[:2]

    predictor = select_predictor(prefer=prefer)
    saliency = predictor.predict(image_rgb)
    if saliency.shape != (h, w):
        # Resize to original if model output a different size
        import cv2

        saliency = cv2.resize(saliency, (w, h), interpolation=cv2.INTER_CUBIC)
        saliency = _normalize(saliency)

    heatmap_path = out_dir / f"{label}_heatmap.png"
    saliency_path = out_dir / f"{label}_saliency.png"
    aoi_path = out_dir / f"{label}_aoi.json"

    save_overlay(image_rgb, saliency, heatmap_path)
    save_grayscale(saliency, saliency_path)

    aois = extract_aois(saliency, top_n=top_n)

    manifest = {
        "label": label,
        "screenshot": str(screenshot),
        "predictor": predictor.name,
        "viewport": {"width": w, "height": h},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {
            "heatmap_overlay": str(heatmap_path),
            "saliency_grayscale": str(saliency_path),
            "aoi_json": str(aoi_path),
        },
        "aois": aois,
    }
    with open(aoi_path, "w") as fh:
        json.dump(manifest, fh, indent=2)

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Generate a saliency heatmap and AOI JSON for a UI screenshot."
    )
    parser.add_argument("--screenshot", required=True, type=Path, help="Path to PNG/JPG screenshot")
    parser.add_argument(
        "--out", required=True, type=Path, help="Output directory for heatmap + json"
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Filename label (default: screenshot basename without extension)",
    )
    parser.add_argument(
        "--predictor",
        choices=["auto", "ueyes", "deepgaze", "opencv"],
        default="auto",
        help="Predictor preference (default: auto = best available)",
    )
    parser.add_argument(
        "--top-n", type=int, default=5, help="Number of top AOIs to return (default: 5)"
    )
    args = parser.parse_args()

    label = args.label or args.screenshot.stem
    manifest = run(
        screenshot=args.screenshot,
        out_dir=args.out,
        label=label,
        prefer=args.predictor,
        top_n=args.top_n,
    )

    print(f"\n{'='*60}")
    print(f"Predictor used:    {manifest['predictor']}")
    print(f"Viewport:          {manifest['viewport']['width']}x{manifest['viewport']['height']}")
    print(f"Heatmap overlay:   {manifest['outputs']['heatmap_overlay']}")
    print(f"Saliency map:      {manifest['outputs']['saliency_grayscale']}")
    print(f"AOI manifest:      {manifest['outputs']['aoi_json']}")
    print(f"Top {len(manifest['aois'])} AOIs:")
    for aoi in manifest["aois"]:
        print(
            f"  #{aoi['rank']:>1}  zone={aoi['zone']:>12}  "
            f"share={aoi['share_of_attention']:.1%}  "
            f"bbox={aoi['bbox']}"
        )
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
