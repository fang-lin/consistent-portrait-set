#!/usr/bin/env python3
"""
Photo Suite Generator — Consistent 4-photo set pipeline.

Steps:
  generate  — Call Gemini to create a 2x2 grid image (default 4K, 9:16)
  crop      — Split grid into 4 individual images
  upscale   — Upscale individual images via Gemini (optional)
  finalize  — Move crops to output directory (skip upscale)

Usage:
  python generate_suite.py --step generate --model-card ref.jpg --prompt "..." --session-id 20260426_120000
  python generate_suite.py --step crop --session-id 20260426_120000
  python generate_suite.py --step upscale --session-id 20260426_120000 --resolution 4K
  python generate_suite.py --step finalize --session-id 20260426_120000
"""

import argparse
import datetime
import json
import logging
import os
import shutil
import sys

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_RESOLUTION = "4K"
DEFAULT_ASPECT_RATIO = "9:16"
VALID_RESOLUTIONS = ["512", "1K", "2K", "4K"]
VALID_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1",
    "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
]

BASE_DIR = os.path.expanduser("~/.hermes/profiles/alice/workspace/photo-suite")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
LOG_DIR = os.path.join(BASE_DIR, "logs")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(session_id: str) -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    log_file = os.path.join(LOG_DIR, f"{today}.log")

    logger = logging.getLogger("photo-suite")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(sh)

    return logger


# ---------------------------------------------------------------------------
# Gemini API via google-genai SDK
# ---------------------------------------------------------------------------

def call_gemini(
    prompt: str,
    reference_images: list[str] = None,
    model: str = None,
    resolution: str = None,
    aspect_ratio: str = None,
) -> dict:
    """Call Gemini API using google-genai SDK.

    Args:
        prompt: Text prompt
        reference_images: List of file paths to reference images
        model: Gemini model ID
        resolution: Output resolution — "512", "1K", "2K", or "4K"
        aspect_ratio: Output aspect ratio — e.g. "9:16", "16:9", "1:1"

    Returns:
        dict with 'image_path' (str or None) and 'text' (str)
    """
    from google import genai
    from google.genai import types
    import base64
    import uuid

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    client = genai.Client(api_key=GEMINI_API_KEY)
    model = model or DEFAULT_MODEL

    # Build content parts
    parts = []

    # Add reference images
    for img_path in (reference_images or []):
        with open(img_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(img_path)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/jpeg")
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    # Add text prompt
    parts.append(types.Part.from_text(text=prompt))

    # Build image config
    image_config_kwargs = {}
    if resolution and resolution in VALID_RESOLUTIONS:
        image_config_kwargs["image_size"] = resolution
    if aspect_ratio and aspect_ratio in VALID_ASPECT_RATIOS:
        image_config_kwargs["aspect_ratio"] = aspect_ratio

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(**image_config_kwargs) if image_config_kwargs else None,
    )

    # Call API
    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=config,
    )

    if not response.candidates:
        raise RuntimeError("No candidates in Gemini response")

    # Extract results
    image_path = None
    text = ""

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            img_data = base64.b64decode(part.inline_data.data) if isinstance(part.inline_data.data, str) else part.inline_data.data
            mime = part.inline_data.mime_type or "image/png"
            ext = ".png" if "png" in mime else ".jpg" if "jpeg" in mime else ".webp" if "webp" in mime else ".png"
            image_path = os.path.join(TMP_DIR, f"_gemini_out_{uuid.uuid4().hex[:8]}{ext}")
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(img_data)
        elif part.text:
            text += part.text

    return {"image_path": image_path, "text": text}


# ---------------------------------------------------------------------------
# Step 1: Generate grid
# ---------------------------------------------------------------------------

def step_generate(args, logger):
    session_dir = os.path.join(TMP_DIR, args.session_id)
    os.makedirs(session_dir, exist_ok=True)

    refs = []
    if args.model_card:
        refs.append(args.model_card)
    if args.env_ref:
        refs.append(args.env_ref)
    if args.outfit_ref:
        refs.append(args.outfit_ref)
    if args.accessory_ref:
        refs.append(args.accessory_ref)

    if not args.prompt:
        print("ERROR: --prompt required for generate step")
        sys.exit(1)

    resolution = args.resolution or DEFAULT_RESOLUTION
    aspect_ratio = args.aspect_ratio or DEFAULT_ASPECT_RATIO

    logger.info(f"[generate] session={args.session_id} refs={len(refs)} resolution={resolution} ar={aspect_ratio} prompt={args.prompt[:80]}...")

    start = datetime.datetime.now()
    result = call_gemini(
        args.prompt,
        reference_images=refs,
        model=args.model,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
    )
    elapsed = (datetime.datetime.now() - start).total_seconds()

    if not result["image_path"]:
        logger.error("[generate] No image returned from Gemini")
        print("ERROR: No image returned from Gemini")
        if result["text"]:
            print(f"Model response: {result['text']}")
        sys.exit(1)

    # Move to session dir
    grid_path = os.path.join(session_dir, "grid.png")
    os.rename(result["image_path"], grid_path)

    # Log actual image dimensions
    from PIL import Image
    img = Image.open(grid_path)
    w, h = img.size

    logger.info(f"[generate] Grid saved: {grid_path} ({w}x{h}, {elapsed:.1f}s)")
    if result["text"]:
        logger.info(f"[generate] Model text: {result['text'][:200]}")

    print(f"Grid generated: {grid_path}")
    print(f"Resolution: {w}x{h}")
    print(f"Time: {elapsed:.1f}s")


# ---------------------------------------------------------------------------
# Step 2: Crop
# ---------------------------------------------------------------------------

def step_crop(args, logger):
    from PIL import Image

    session_dir = os.path.join(TMP_DIR, args.session_id)
    grid_path = os.path.join(session_dir, "grid.png")

    if not os.path.exists(grid_path):
        print(f"ERROR: Grid not found at {grid_path}")
        sys.exit(1)

    img = Image.open(grid_path)
    w, h = img.size
    half_w, half_h = w // 2, h // 2

    crops = {
        "crop-1.png": (0, 0, half_w, half_h),           # top-left
        "crop-2.png": (half_w, 0, w, half_h),            # top-right
        "crop-3.png": (0, half_h, half_w, h),            # bottom-left
        "crop-4.png": (half_w, half_h, w, h),            # bottom-right
    }

    logger.info(f"[crop] session={args.session_id} grid={w}x{h} each={half_w}x{half_h}")

    paths = []
    for name, box in crops.items():
        cropped = img.crop(box)
        path = os.path.join(session_dir, name)
        cropped.save(path, quality=95)
        paths.append(path)
        logger.info(f"[crop] Saved: {path} ({half_w}x{half_h})")

    print(f"Cropped 4 images from {w}x{h} grid (each {half_w}x{half_h}):")
    for p in paths:
        print(f"  {p}")


# ---------------------------------------------------------------------------
# Step 3: Upscale (optional)
# ---------------------------------------------------------------------------

def step_upscale(args, logger):
    session_dir = os.path.join(TMP_DIR, args.session_id)
    today = datetime.date.today().isoformat()

    if args.image_index:
        indices = [args.image_index]
    else:
        indices = [1, 2, 3, 4]

    today_dir = os.path.join(OUTPUT_DIR, today)
    existing = [d for d in os.listdir(today_dir) if d.startswith("set-")] if os.path.exists(today_dir) else []
    set_num = len(existing) + 1
    out_dir = os.path.join(today_dir, f"set-{set_num:03d}")
    os.makedirs(out_dir, exist_ok=True)

    resolution = args.resolution or "4K"
    prompt = args.upscale_prompt or "Upscale this image to high resolution. Preserve all details faithfully. Maintain exact facial features, hand proportions (5 fingers each), clothing texture, and background details."

    for idx in indices:
        crop_path = os.path.join(session_dir, f"crop-{idx}.png")
        if not os.path.exists(crop_path):
            print(f"ERROR: crop-{idx}.png not found")
            continue

        refs = [crop_path]
        if args.upscale_ref:
            refs.append(args.upscale_ref)

        logger.info(f"[upscale] image={idx} refs={len(refs)} resolution={resolution} prompt={prompt[:60]}...")

        start = datetime.datetime.now()
        result = call_gemini(prompt, reference_images=refs, model=args.model, resolution=resolution)
        elapsed = (datetime.datetime.now() - start).total_seconds()

        if result["image_path"]:
            final_path = os.path.join(out_dir, f"final-{idx}.png")
            os.rename(result["image_path"], final_path)

            from PIL import Image
            img = Image.open(final_path)
            w, h = img.size

            logger.info(f"[upscale] Saved: {final_path} ({w}x{h}, {elapsed:.1f}s)")
            print(f"Upscaled image {idx}: {final_path} ({w}x{h}, {elapsed:.1f}s)")
        else:
            logger.error(f"[upscale] No image returned for crop-{idx}")
            print(f"ERROR: No image returned for crop-{idx}")
            if result["text"]:
                print(f"Model response: {result['text'][:200]}")

    print(f"\nOutput directory: {out_dir}")


# ---------------------------------------------------------------------------
# Step 4: Finalize (skip upscale)
# ---------------------------------------------------------------------------

def step_finalize(args, logger):
    session_dir = os.path.join(TMP_DIR, args.session_id)
    today = datetime.date.today().isoformat()

    today_dir = os.path.join(OUTPUT_DIR, today)
    existing = [d for d in os.listdir(today_dir) if d.startswith("set-")] if os.path.exists(today_dir) else []
    set_num = len(existing) + 1
    out_dir = os.path.join(today_dir, f"set-{set_num:03d}")
    os.makedirs(out_dir, exist_ok=True)

    for idx in range(1, 5):
        crop_path = os.path.join(session_dir, f"crop-{idx}.png")
        if not os.path.exists(crop_path):
            print(f"ERROR: crop-{idx}.png not found")
            continue
        final_path = os.path.join(out_dir, f"final-{idx}.png")
        shutil.copy2(crop_path, final_path)

        from PIL import Image
        img = Image.open(final_path)
        w, h = img.size
        logger.info(f"[finalize] Copied: {final_path} ({w}x{h})")
        print(f"Final image {idx}: {final_path} ({w}x{h})")

    print(f"\nOutput directory: {out_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Photo Suite Generator")
    parser.add_argument("--step", required=True, choices=["generate", "crop", "upscale", "finalize"])
    parser.add_argument("--session-id", required=True, help="Session identifier for file organization")
    parser.add_argument("--model", default=None, help=f"Gemini model (default: {DEFAULT_MODEL})")
    parser.add_argument("--resolution", default=None, help=f"Output resolution: {', '.join(VALID_RESOLUTIONS)} (default: {DEFAULT_RESOLUTION})")
    parser.add_argument("--aspect-ratio", default=None, help=f"Aspect ratio (default: {DEFAULT_ASPECT_RATIO}). Valid: {', '.join(VALID_ASPECT_RATIOS)}")

    # Generate args
    parser.add_argument("--model-card", default=None, help="Path to model card (face reference)")
    parser.add_argument("--prompt", default=None, help="Generation prompt")
    parser.add_argument("--env-ref", default=None, help="Environment reference image (optional)")
    parser.add_argument("--outfit-ref", default=None, help="Outfit reference image (optional)")
    parser.add_argument("--accessory-ref", default=None, help="Accessory reference image (optional)")

    # Upscale args
    parser.add_argument("--upscale-prompt", default=None, help="Custom upscale prompt")
    parser.add_argument("--upscale-ref", default=None, help="Additional reference image for upscale (optional)")
    parser.add_argument("--image-index", type=int, default=None, help="Upscale specific image (1-4), omit for all")

    args = parser.parse_args()

    if not GEMINI_API_KEY and args.step not in ("crop", "finalize"):
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    if args.resolution and args.resolution not in VALID_RESOLUTIONS:
        print(f"ERROR: Invalid resolution '{args.resolution}'. Valid: {', '.join(VALID_RESOLUTIONS)}")
        sys.exit(1)

    if args.aspect_ratio and args.aspect_ratio not in VALID_ASPECT_RATIOS:
        print(f"ERROR: Invalid aspect ratio '{args.aspect_ratio}'. Valid: {', '.join(VALID_ASPECT_RATIOS)}")
        sys.exit(1)

    logger = setup_logging(args.session_id)

    if args.step == "generate":
        step_generate(args, logger)
    elif args.step == "crop":
        step_crop(args, logger)
    elif args.step == "upscale":
        step_upscale(args, logger)
    elif args.step == "finalize":
        step_finalize(args, logger)


if __name__ == "__main__":
    main()
