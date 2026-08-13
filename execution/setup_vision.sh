#!/usr/bin/env bash
# One-time setup for the saliency / heatmap pipeline used by the
# heatmap_analyst skill.
#
# What it does:
#   1. Creates execution/.venv-vision/ (isolated venv)
#   2. Installs hard deps (numpy, Pillow, opencv) so the OpenCV fallback works.
#   3. OPTIONALLY installs PyTorch + deepgaze-pytorch (better fidelity).
#   4. OPTIONALLY clones UEyes weights into .models/ueyes/ (UI-trained).
#   5. Runs a smoke test on a synthetic image, prints status per predictor.
#
# Re-running is safe — every step is idempotent.

set -euo pipefail

EXEC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$EXEC_DIR/.venv-vision"
MODELS_DIR="$EXEC_DIR/.models"
SMOKE_DIR="$EXEC_DIR/.smoke"

echo "==> Setup vision stack at $EXEC_DIR"

# ----- 1. venv ---------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating venv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --quiet --upgrade pip

# ----- 2. hard deps ----------------------------------------------------------
echo "==> Installing hard deps (numpy, Pillow, opencv)"
pip install --quiet -r "$EXEC_DIR/requirements_vision.txt"

# ----- 3. optional: DeepGaze IIE --------------------------------------------
INSTALL_DEEPGAZE="${INSTALL_DEEPGAZE:-1}"
if [ "$INSTALL_DEEPGAZE" = "1" ]; then
    echo "==> Installing optional DeepGaze IIE (PyTorch + deepgaze-pytorch)"
    echo "    (set INSTALL_DEEPGAZE=0 to skip; OpenCV fallback still works)"
    pip install --quiet torch torchvision || {
        echo "    [warn] torch install failed — DeepGaze unavailable, OpenCV fallback only"
    }
    pip install --quiet deepgaze-pytorch || {
        echo "    [warn] deepgaze-pytorch install failed — OpenCV fallback only"
    }
fi

# ----- 4. optional: UEyes weights -------------------------------------------
INSTALL_UEYES="${INSTALL_UEYES:-0}"
if [ "$INSTALL_UEYES" = "1" ]; then
    echo "==> Installing optional UEyes (UI-trained saliency)"
    mkdir -p "$MODELS_DIR/ueyes"
    if [ ! -f "$MODELS_DIR/ueyes/ueyes_model.py" ]; then
        echo "    Clone UEyes-CHI2023 into $MODELS_DIR/ueyes/"
        echo "    -> https://github.com/YueJiang-nj/UEyes-CHI2023"
        echo "    Then download the pretrained weights from the repo's releases"
        echo "    and place them in $MODELS_DIR/ueyes/."
        echo "    UEyes is OPTIONAL — DeepGaze + OpenCV already produce usable heatmaps."
    else
        echo "    UEyes already present at $MODELS_DIR/ueyes/"
    fi
fi

# ----- 5. smoke test ---------------------------------------------------------
echo "==> Smoke test"
mkdir -p "$SMOKE_DIR"
SMOKE_INPUT="$SMOKE_DIR/smoke_input.png"

# Synthesize a 1440x900 fake landing-page-ish image with a bright hero block,
# a darker secondary, and some noise — enough to exercise the saliency model.
python - <<PY
from pathlib import Path
import numpy as np
from PIL import Image
img = np.full((900, 1440, 3), 245, dtype=np.uint8)  # near-white bg
img[120:380, 120:760] = (232, 115, 74)               # hero block (#E8734A-ish)
img[120:380, 800:1320] = (235, 235, 240)             # right column
img[460:560, 120:380] = (32, 32, 38)                 # dark cta
img[640:800, 120:1320] = (250, 246, 240)             # footer band
Image.fromarray(img).save("$SMOKE_INPUT")
print(f"  wrote synthetic input -> $SMOKE_INPUT")
PY

for predictor in auto opencv; do
    label="smoke_${predictor}"
    echo "  -> predictor=$predictor"
    python "$EXEC_DIR/predict_attention.py" \
        --screenshot "$SMOKE_INPUT" \
        --out "$SMOKE_DIR" \
        --label "$label" \
        --predictor "$predictor" \
        --top-n 3 || {
            echo "    [warn] $predictor predictor failed"
        }
done

echo
echo "==> Setup complete."
echo "    To use:"
echo "      source $VENV_DIR/bin/activate"
echo "      python $EXEC_DIR/predict_attention.py \\"
echo "          --screenshot path/to/screenshot.png \\"
echo "          --out ./assets/heatmaps/ \\"
echo "          --label landing_desktop"
echo
echo "    Predictor preference: pass --predictor [auto|ueyes|deepgaze|opencv]"
