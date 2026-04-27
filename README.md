# consistent-portrait-set

> Generate consistent multi-photo portrait sets with face-locked model cards.

An agent skill for [Hermes Agent](https://hermes-agent.nousresearch.com/) that generates consistent portrait photo sets using Google Gemini's image generation API. Supports reference images for face-locking, environment, outfit, and accessories.

## Features

- **Grid Mode**: Generate a 2x2 grid of 4 portraits in one API call, then crop into individual images
- **Chain Mode**: Generate images one at a time with per-image review, no limit on count
- **Face-locking**: Use a model card (reference photo) to maintain consistent facial features
- **Flexible references**: Optional environment, outfit, and accessory reference images
- **Resolution control**: 512, 1K, 2K, 4K output support via Gemini API
- **Aspect ratio control**: 9:16 default (portrait), 14 ratios supported
- **Quality approval gates**: Creative brief → prompt review → image review
- **Organized file management**: Structured tmp/outputs/logs directories with session-based naming

## Requirements

- [Hermes Agent](https://hermes-agent.nousresearch.com/) with `code_execution` and `skills` toolsets enabled
- Google Gemini API key (`GEMINI_API_KEY` environment variable)
- Python packages: `google-genai`, `Pillow`

## Installation

```bash
hermes skills install github/fang-lin/consistent-portrait-set
```

Or manually copy to your Hermes skills directory:

```bash
cp -r consistent-portrait-set ~/.hermes/skills/
```

## Usage

Once installed, the agent will automatically load this skill when you ask for photo sets. Examples:

- "Generate a photo set for me"
- "I want 4 portraits in business casual"
- "Give me a set of street fashion shots"

The skill guides the agent through a structured workflow:

1. **Creative Brief** — Agent proposes theme, mood, trending topics
2. **Gather Inputs** — Model card + optional reference images
3. **Compose Prompt** — Agent builds detailed generation prompt
4. **Prompt Approval** — User reviews prompt before generation
5. **Generate** — Grid or Chain mode via Gemini API
6. **Image Approval** — User reviews generated images
7. **Crop/Finalize** — Process and organize output files
8. **Deliver** — Final images sent to user

## Modes

### Grid Mode
Generates a 2x2 grid image, crops into 4 individual portraits. Fast and cost-effective.
- Default: 4K grid → ~2K per crop
- Cost: ~$0.151 per grid (Gemini 3.1 Flash Image)

### Chain Mode
Generates portraits one at a time. Each image can use previous images as references for consistency. Unlimited count, per-image approval.
- Default: 2K per image
- Cost: ~$0.101 per image (Gemini 3.1 Flash Image)

## Supported Models

- `gemini-3.1-flash-image-preview` (default) — best price/quality
- `gemini-3-pro-image-preview` — highest quality
- `gemini-2.5-flash-image` — cheapest

## License

MIT
