#!/usr/bin/env python3
"""
Logo Generation Engine — Design Agency
Generates logo concept images using Google Gemini 3.1 Flash Image Preview and Imagen 4.0 APIs.
Produces 6 options per concept with metadata logging for self-improvement.

Models:
    - gemini-3.1-flash-image-preview: Multimodal LLM with image generation, best for
      concept-aware generation that understands spatial relationships and metaphors.
    - imagen-4.0-generate-001: Dedicated image model, fast batch generation (up to 4/call).

Usage:
    python generate_logo.py --concept "minimal geometric mark for fintech" \
                            --brand "Acme" \
                            --style "modern, clean, geometric" \
                            --colors "#1A1A2E,#16213E,#0F3460,#E94560" \
                            --output ./output_dir

Environment:
    GEMINI_API_KEY or GOOGLE_API_KEY must be set.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def get_api_key():
    """Resolve API key from environment."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        # Check .env file in project root
        env_paths = [
            Path(__file__).parent.parent / ".env",
            Path(__file__).parent.parent / ".env.local",
            Path.home() / ".env",
        ]
        for env_path in env_paths:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
                        elif line.startswith("GOOGLE_API_KEY="):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
                if key:
                    break
    return key


def build_logo_prompt(concept, brand, style, colors, typography, iteration_context=None):
    """
    Build a detailed logo generation prompt.
    Incorporates concept, brand attributes, style directive, and past feedback.
    """
    color_str = ", ".join(colors) if colors else "brand-appropriate colors"
    typo_str = typography if typography else "clean, modern typeface"

    prompt = f"""Generate a professional logo design for "{brand}".

CONCEPT: {concept}

STYLE REQUIREMENTS:
- Visual style: {style}
- Color palette: ONLY use these exact colors: {color_str}
- Typography direction: {typo_str}
- The logo must work as a standalone icon/mark AND with the brand name
- Clean vector-like quality, suitable for professional branding — sharp edges, no blur
- High contrast, works on both light and dark backgrounds
- No photorealistic elements — this is a logo, not a photograph
- Flat or minimal depth, professional brand mark quality
- No text artifacts or garbled letters — if text is included, it must be crisp and perfectly legible
- No gradients unless explicitly part of the concept
- No decorative flourishes, swirls, or ornaments
- The mark should be recognizable at 24px (favicon) and 200px (hero)

OUTPUT: A single, centered logo on a clean white background (#FFFFFF). No background patterns, no frames, no decorative borders. The design should be memorable, distinctive, and ownable — not a generic icon that could belong to any company."""

    if iteration_context:
        prompt += f"""

ITERATION CONTEXT (learn from previous feedback):
{iteration_context}"""

    return prompt


def generate_with_gemini(client, prompt, output_dir, concept_idx, option_idx, config_overrides=None):
    """
    Generate a single logo image using Gemini Nano Banana model.
    Returns metadata dict or None on failure.
    """
    from google.genai import types

    model = config_overrides.get("model", "gemini-3.1-flash-image-preview") if config_overrides else "gemini-3.1-flash-image-preview"

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        saved_path = None
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                ext = "png" if "png" in part.inline_data.mime_type else "jpg"
                filename = f"concept_{concept_idx:02d}_option_{option_idx:02d}.{ext}"
                filepath = output_dir / filename

                with open(filepath, "wb") as f:
                    f.write(part.inline_data.data)

                saved_path = str(filepath)
                print(f"  [OK] Saved: {filename}")
                break

        if not saved_path:
            print(f"  [WARN] No image in response for option {option_idx}")
            return None

        return {
            "file": saved_path,
            "model": model,
            "engine": "gemini-nano-banana",
            "concept_idx": concept_idx,
            "option_idx": option_idx,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        print(f"  [ERROR] Gemini generation failed for option {option_idx}: {e}")
        return None


def generate_with_imagen(client, prompt, output_dir, concept_idx, batch_start, count, config_overrides=None):
    """
    Generate a batch of logo images using Imagen API.
    Returns list of metadata dicts.
    """
    from google.genai import types

    model = config_overrides.get("imagen_model", "imagen-4.0-generate-001") if config_overrides else "imagen-4.0-generate-001"
    aspect = config_overrides.get("aspect_ratio", "1:1") if config_overrides else "1:1"

    actual_count = min(count, 4)  # Imagen max is 4 per request

    try:
        response = client.models.generate_images(
            model=model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=actual_count,
                aspect_ratio=aspect,
            ),
        )

        results = []
        for i, generated_image in enumerate(response.generated_images):
            option_idx = batch_start + i
            filename = f"concept_{concept_idx:02d}_option_{option_idx:02d}.png"
            filepath = output_dir / filename

            img = generated_image.image
            img.save(str(filepath))
            print(f"  [OK] Saved: {filename}")

            results.append({
                "file": str(filepath),
                "model": model,
                "engine": "imagen",
                "concept_idx": concept_idx,
                "option_idx": option_idx,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return results

    except Exception as e:
        print(f"  [ERROR] Imagen generation failed: {e}")
        return []


def generate_concept(client, concept, brand, style, colors, typography,
                     concept_idx, output_dir, options_count=6,
                     engine="gemini", config_overrides=None, iteration_context=None):
    """
    Generate all options for a single concept.
    Handles both Gemini and Imagen engines, including fallback.
    """
    prompt = build_logo_prompt(concept, brand, style, colors, typography, iteration_context)
    results = []

    print(f"\n--- Concept {concept_idx}: {concept[:60]}... ---")
    print(f"    Engine: {engine} | Options: {options_count}")

    if engine == "imagen":
        # Imagen: max 4 per call, so split into batches
        remaining = options_count
        batch_start = 1
        while remaining > 0:
            batch_size = min(remaining, 4)
            batch_results = generate_with_imagen(
                client, prompt, output_dir, concept_idx,
                batch_start, batch_size, config_overrides
            )
            results.extend(batch_results)
            batch_start += batch_size
            remaining -= batch_size
            if remaining > 0:
                time.sleep(1)  # Rate limit courtesy

    elif engine == "gemini":
        # Gemini Nano Banana: 1 image per call, loop for all options
        for opt in range(1, options_count + 1):
            # Vary the prompt slightly for diversity
            variation_hint = _get_variation_hint(opt)
            varied_prompt = prompt + f"\n\nVARIATION DIRECTION: {variation_hint}"

            result = generate_with_gemini(
                client, varied_prompt, output_dir, concept_idx, opt, config_overrides
            )
            if result:
                result["variation"] = variation_hint
                results.append(result)

            if opt < options_count:
                time.sleep(1.5)  # Rate limit courtesy for sequential calls

    elif engine == "both":
        # Use Imagen for first 4, Gemini for last 2 (diversity)
        print("  Phase 1: Imagen batch (4 options)...")
        imagen_results = generate_with_imagen(
            client, prompt, output_dir, concept_idx, 1, 4, config_overrides
        )
        results.extend(imagen_results)

        print("  Phase 2: Gemini variations (2 options)...")
        for opt in range(5, options_count + 1):
            variation_hint = _get_variation_hint(opt)
            varied_prompt = prompt + f"\n\nVARIATION DIRECTION: {variation_hint}"
            result = generate_with_gemini(
                client, varied_prompt, output_dir, concept_idx, opt, config_overrides
            )
            if result:
                result["variation"] = variation_hint
                results.append(result)
            time.sleep(1.5)

    return results


def _get_variation_hint(option_num):
    """Generate variation hints to ensure diversity across the 6 options."""
    variations = [
        "Bold and confident — heavy strokes, strong presence, maximum impact, thick line weight",
        "Minimal and refined — stripped to essentials, elegant negative space, thin precise lines",
        "Geometric and structured — precise shapes, mathematical harmony, grid-based construction",
        "Organic and fluid — natural curves, approachable warmth, rounded forms",
        "Typographic-led — the letterforms ARE the mark, creative type treatment, no separate icon",
        "Abstract symbol — pure iconography, universally recognizable mark, no text",
        "Monogram/lettermark — initials as art, sophisticated abbreviation, contained composition",
        "Emblem style — contained mark with integrated text, badge-like authority, unified shape",
    ]
    idx = (option_num - 1) % len(variations)
    return variations[idx]


def load_feedback_log(log_path):
    """Load the self-improvement feedback log."""
    if log_path.exists():
        with open(log_path) as f:
            return json.load(f)
    return {"sessions": [], "learnings": [], "prompt_patterns": {"effective": [], "ineffective": []}}


def save_feedback_log(log_path, log_data):
    """Save the feedback log."""
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)


def build_iteration_context(feedback_log, brand):
    """
    Build iteration context from past feedback for this brand.
    This is the self-improvement mechanism.
    """
    if not feedback_log.get("sessions"):
        return None

    brand_sessions = [s for s in feedback_log["sessions"] if s.get("brand") == brand]
    if not brand_sessions:
        return None

    context_parts = []

    # Gather effective patterns
    effective = feedback_log.get("prompt_patterns", {}).get("effective", [])
    if effective:
        context_parts.append("PATTERNS THAT WORKED WELL:")
        for p in effective[-5:]:  # Last 5
            context_parts.append(f"  - {p}")

    # Gather things to avoid
    ineffective = feedback_log.get("prompt_patterns", {}).get("ineffective", [])
    if ineffective:
        context_parts.append("PATTERNS TO AVOID:")
        for p in ineffective[-5:]:
            context_parts.append(f"  - {p}")

    # Gather learnings
    learnings = feedback_log.get("learnings", [])
    if learnings:
        context_parts.append("KEY LEARNINGS:")
        for l in learnings[-5:]:
            context_parts.append(f"  - {l}")

    return "\n".join(context_parts) if context_parts else None


def log_session(feedback_log, brand, concepts, engine, results_count, selected_options=None, feedback=None):
    """Log a generation session for future improvement."""
    session = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brand": brand,
        "concepts": concepts,
        "engine": engine,
        "options_generated": results_count,
        "selected_options": selected_options,
        "feedback": feedback,
    }
    feedback_log["sessions"].append(session)
    return feedback_log


def main():
    parser = argparse.ArgumentParser(
        description="Generate logo concepts using Gemini/Imagen AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 6 options for one concept
  python generate_logo.py --concept "geometric owl mark" --brand "Acme" \\
      --style "modern fintech" --colors "#1A1A2E,#E94560" --output ./logos

  # Multiple concepts (6 options each)
  python generate_logo.py --concepts-file concepts.json --brand "Acme" --output ./logos

  # Log feedback for self-improvement
  python generate_logo.py --log-feedback --brand "Acme" \\
      --selected "concept_01_option_03,concept_02_option_01" \\
      --feedback "Client preferred geometric over organic. Bolder strokes resonated."
        """,
    )

    parser.add_argument("--concept", type=str, help="Single concept description")
    parser.add_argument("--concepts-file", type=str, help="JSON file with multiple concepts")
    parser.add_argument("--brand", type=str, required=True, help="Brand name")
    parser.add_argument("--style", type=str, default="modern, professional", help="Style keywords")
    parser.add_argument("--colors", type=str, default="", help="Comma-separated hex colors")
    parser.add_argument("--typography", type=str, default="", help="Typography direction")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--options", type=int, default=6, help="Options per concept (default: 6)")
    parser.add_argument("--engine", choices=["gemini", "imagen", "both"], default="gemini",
                        help="Generation engine (default: gemini)")
    parser.add_argument("--model", type=str, help="Override model name")
    parser.add_argument("--aspect-ratio", type=str, default="1:1",
                        help="Aspect ratio for Imagen (default: 1:1)")

    # Feedback/self-improvement commands
    parser.add_argument("--log-feedback", action="store_true", help="Log feedback for self-improvement")
    parser.add_argument("--selected", type=str, help="Comma-separated selected option filenames")
    parser.add_argument("--feedback", type=str, help="User/client feedback text")
    parser.add_argument("--learning", type=str, help="Add a learning to the feedback log")

    args = parser.parse_args()

    # Resolve the feedback-log path via the plugin's state-path helper so it
    # follows the env / repo-local / fallback chain instead of assuming the log
    # lives next to this script.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from state_paths import resolve
    feedback_log_path = Path(resolve("logo_feedback_log.json"))
    output_dir = Path(args.output)

    # Handle feedback logging mode
    if args.log_feedback:
        log = load_feedback_log(feedback_log_path)

        if args.feedback:
            log = log_session(log, args.brand, [], "", 0,
                              selected_options=args.selected.split(",") if args.selected else None,
                              feedback=args.feedback)
            print(f"Logged feedback for {args.brand}")

        if args.learning:
            log.setdefault("learnings", []).append(args.learning)
            print(f"Added learning: {args.learning}")

        save_feedback_log(feedback_log_path, log)
        return

    # Validate we have a concept to generate
    if not args.concept and not args.concepts_file:
        print("Error: Provide --concept or --concepts-file")
        sys.exit(1)

    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("Error: No API key found.")
        print("Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable,")
        print("or create a .env file in the project root.")
        sys.exit(1)

    # Initialize client
    from google import genai
    client = genai.Client(api_key=api_key)

    # Load concepts
    concepts = []
    if args.concept:
        concepts = [args.concept]
    elif args.concepts_file:
        with open(args.concepts_file) as f:
            data = json.load(f)
            concepts = data if isinstance(data, list) else data.get("concepts", [])

    colors = [c.strip() for c in args.colors.split(",") if c.strip()]

    # Config overrides
    config_overrides = {"aspect_ratio": args.aspect_ratio}
    if args.model:
        config_overrides["model"] = args.model
        config_overrides["imagen_model"] = args.model

    # Load feedback log for self-improvement context
    feedback_log = load_feedback_log(feedback_log_path)
    iteration_context = build_iteration_context(feedback_log, args.brand)

    if iteration_context:
        print("Loaded self-improvement context from previous sessions.")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate for each concept
    all_results = []
    for idx, concept in enumerate(concepts, 1):
        concept_text = concept if isinstance(concept, str) else concept.get("description", str(concept))
        results = generate_concept(
            client=client,
            concept=concept_text,
            brand=args.brand,
            style=args.style,
            colors=colors,
            typography=args.typography,
            concept_idx=idx,
            output_dir=output_dir,
            options_count=args.options,
            engine=args.engine,
            config_overrides=config_overrides,
            iteration_context=iteration_context,
        )
        all_results.extend(results)

    # Save generation manifest
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brand": args.brand,
        "engine": args.engine,
        "concepts": concepts,
        "style": args.style,
        "colors": colors,
        "typography": args.typography,
        "options_per_concept": args.options,
        "total_generated": len(all_results),
        "results": all_results,
    }
    manifest_path = output_dir / "generation_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Log session
    feedback_log = log_session(feedback_log, args.brand, concepts, args.engine, len(all_results))
    save_feedback_log(feedback_log_path, feedback_log)

    print(f"\n{'='*50}")
    print(f"Generated {len(all_results)} logo options across {len(concepts)} concept(s)")
    print(f"Output: {output_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
