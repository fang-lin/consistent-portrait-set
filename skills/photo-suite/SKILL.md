---
name: photo-suite
description: Generate consistent photo sets using a model card for face-locking. Two modes — Grid Mode (4-photo grid) and Chain Mode (sequential, unlimited). Use when moom asks for photo sets, beauty shots, outfit photos, or套图.
version: 0.8.0
requires_toolsets:
  - code_execution
  - skills
env:
  - GEMINI_API_KEY
---

# Photo Suite — Consistent 4-Photo Set Generator

Generate a set of 4 consistent photos from a single model card (face reference),
with customizable outfits, environments, and accessories.

## CRITICAL RULES

> [!IMPORTANT]
> 1. **ALL steps MUST be executed through `generate_suite.py` script.** Do NOT write your own code to call Gemini API, crop images, or upscale. The script handles directory structure, logging, and file management.
> 2. **Script location:** Find it at `~/.hermes/profiles/alice/skills/photo-suite/scripts/generate_suite.py` or `~/.hermes/skills/photo-suite/scripts/generate_suite.py`
> 3. **Send images via `MEDIA:` prefix only.** Never use browser_navigate or any other method to show images.
> 4. **Three approval gates: creative brief (Step 1), prompt (Step 4), and grid image (Step 6). Do NOT skip any.**
> 5. **All intermediate and output files are managed by the script.** Do not save files to /tmp or any other location manually.

## When to Use

- moom asks for 套图, photo sets, beauty shots, outfit photos, selfie sets
- Any request involving multiple consistent images of the same person

## Workflow

### Step 1: Creative Brief

Before anything else, understand what moom wants and produce a creative brief.

**Two modes — choose based on moom's input:**

**Mode A: moom gives a vague request** (e.g. "给我出一套图", "来点新的")
→ You take the initiative. Use web_search to check current trending topics, seasonal themes, fashion trends. Draft a complete creative brief and present it for approval.

**Mode B: moom gives a specific direction** (e.g. "我想要一套职业装的", "穿红裙子在海边")
→ You ask clarifying questions to fill in the gaps, then confirm the brief.

**The brief format:**

```
📸 套图策划

名称：[套图名称]
主题：[主题/风格关键词]
热点关联：[当下相关的热度话题、节日、流行趋势，没有就写"无"]
场景：[拍摄场景描述]
服装：[服装方向描述]
调性：[清新 / 性感 / 职业 / 街拍 / 文艺 / 暗黑 / ...]
参考说明：[简述创意思路，1-2 句话]
```

**STOP and WAIT for moom to approve, modify, or reject the brief.**

### Step 2: Gather Inputs

**Required:**
- Model card image (face reference) — ask moom which image to use as the model card. Check `~/.hermes/profiles/alice/assets/` for available references, or ask moom to send one.
- Text description from moom (outfit, scene, mood, etc.) — may already be covered in the approved brief

**Optional (ask moom if he wants to provide):**
- Environment/scene reference photo
- Outfit/clothing reference photo
- Shoes/accessories reference photo

### Step 3: Compose Prompt

Build a detailed English prompt for Gemini image generation. The prompt MUST include:

1. **Grid format**: "A strictly equal 2x2 grid, 4 cells of exactly the same size, no overlapping, no irregular layout"
2. **Person description**: Based on model card — describe the face, hair, body type consistently
3. **Outfit**: From moom's description or reference photo
4. **Environment/scene**: From moom's description or reference photo
5. **Pose variety**: Each quadrant should have a different pose/angle
6. **Lighting and mood**: Specify lighting style (natural, studio, golden hour, etc.)
7. **Quality markers**: "high resolution, professional photography, detailed textures"

**Prompt template:**

```
A strictly equal 2x2 grid of 4 portrait photos of [person description]. The grid must have exactly 4 cells of equal size, arranged in 2 rows and 2 columns, with no overlapping or irregular layout. Each cell contains one full portrait photo.

Top-left: [pose/angle 1], [outfit detail], [scene detail]
Top-right: [pose/angle 2], [outfit detail], [scene detail]
Bottom-left: [pose/angle 3], [outfit detail], [scene detail]
Bottom-right: [pose/angle 4], [outfit detail], [scene detail]

Style: [lighting], [mood], professional photography, high resolution, sharp details.
```

### Step 4: Submit Prompt for Approval

> [!IMPORTANT]
> You MUST show the complete prompt to moom BEFORE generating. Do NOT call the API without moom's approval.

Send the composed prompt to moom in a clear format:

```
我准备用以下 prompt 生成四宫格，你看看：

[你组装的完整英文 prompt]

参考图：
- 模特卡：[路径]
- 环境：[路径 or 无]
- 服装：[路径 or 无]
- 饰物：[路径 or 无]

分辨率：4K / AR：9:16

可以吗？
```

**STOP and WAIT for moom to approve, modify, or reject.**

### Step 5: Generate Grid

**MUST use the script. Do NOT call Gemini API directly.**

Default resolution is 4K. The script will output the grid to `tmp/<session-id>/grid.png`.

```python
from hermes_tools import terminal

SCRIPT = "~/.hermes/profiles/alice/skills/photo-suite/scripts/generate_suite.py"

result = terminal(
    f'python {SCRIPT} '
    '--step generate '
    '--model-card /path/to/model-card.jpg '
    '--prompt "your composed prompt here" '
    '--session-id 20260426_120000'
    # Optional reference images — include only if moom provided them:
    # ' --env-ref /path/to/env-ref.jpg'
    # ' --outfit-ref /path/to/outfit-ref.jpg'
    # ' --accessory-ref /path/to/acc-ref.jpg'
    # Optional resolution override (default 4K):
    # ' --resolution 2K'
)
print(result["output"])
```

### Step 6: Send Grid for Approval

> [!IMPORTANT]
> This step is MANDATORY. You MUST send the grid to moom IMMEDIATELY after generation. Do NOT skip this step. Do NOT proceed to crop or any other step without moom's explicit approval.

Send the grid image to moom using `MEDIA:` prefix (this is Hermes's native way to send files in Telegram — just include the path with `MEDIA:` prefix in your response text):

```
MEDIA:<path from script output>/grid.png
```

Ask: "这组四宫格你满意吗？满意我就裁切出图了。"

**STOP and WAIT for moom to approve before proceeding.**

If moom says no:
- Ask what to change
- Adjust prompt and regenerate (go back to Step 4, use same session-id)
- Send the new grid for approval again

### Step 7: Crop

**MUST use the script.**

```python
result = terminal(
    f'python {SCRIPT} '
    '--step crop '
    '--session-id <same session id>'
)
print(result["output"])
```

### Step 8a: Finalize (default — no upscale)

If the 4K grid was used (default), cropped images are already ~2K each. Move them directly to output:

```python
result = terminal(
    f'python {SCRIPT} '
    '--step finalize '
    '--session-id <same session id>'
)
print(result["output"])
```

### Step 8b: Upscale (optional — only if moom requests)

Only use upscale if moom explicitly asks for higher resolution or better detail. Each image can have different settings.

**Upscale prompt guidelines:**
- Base: "Upscale this image to high resolution. Preserve all details faithfully."
- Face emphasis: "Pay special attention to facial features — eyes, skin texture, lip shape. Maintain exact likeness."
- Hands: "Ensure hands have exactly 5 fingers each, natural pose, correct proportions."
- Feet/shoes: "Maintain correct foot proportions and shoe details."
- Clothing: "Preserve fabric texture, pattern details, and color accuracy."
- Background: "Maintain environment details, depth of field, and lighting consistency."

**Reference images during upscale are OPTIONAL and per-image.** Ask moom if he wants to add any.

```python
# Upscale all 4 images to 4K
result = terminal(
    f'python {SCRIPT} '
    '--step upscale '
    '--session-id <same session id> '
    '--resolution 4K '
    '--upscale-prompt "your upscale prompt"'
)
print(result["output"])

# Or upscale a specific image with custom ref and resolution
result = terminal(
    f'python {SCRIPT} '
    '--step upscale '
    '--session-id <same session id> '
    '--resolution 4K '
    '--upscale-prompt "your upscale prompt" '
    '--upscale-ref /path/to/ref.jpg '
    '--image-index 2'
)
print(result["output"])
```

### Step 9: Deliver

Send all 4 final images to moom using MEDIA: prefix. Use the output directory path from the finalize/upscale step:

```
MEDIA:<output-dir>/final-1.png
MEDIA:<output-dir>/final-2.png
MEDIA:<output-dir>/final-3.png
MEDIA:<output-dir>/final-4.png
```

---

## Chain Mode

An alternative to Grid Mode. Generates images one at a time, each with its own approval. No limit on number of images. Best for higher consistency and fine control.

### How to choose

- **Grid Mode**: moom wants a quick set of 4, consistency is acceptable
- **Chain Mode**: moom wants maximum control, each image reviewed, or more/fewer than 4 images

Let moom choose, or suggest based on context.

### Chain Mode Workflow

**Step 1–2**: Same as Grid Mode (Creative Brief + Gather Inputs)

**Step 3: Generate Image 1**

```python
from hermes_tools import terminal

SCRIPT = "~/.hermes/profiles/alice/skills/photo-suite/scripts/generate_suite.py"

result = terminal(
    f'python {SCRIPT} '
    '--step chain '
    '--model-card /path/to/model-card.jpg '
    '--prompt "your prompt for image 1" '
    '--session-id spring_casual_001'
    # Optional: --resolution 4K (default 2K for chain mode)
)
print(result["output"])
```

Send to moom: `MEDIA:<session-dir>/chain-1.png`

Ask: "第 1 张你满意吗？继续下一张？"

**STOP and WAIT for approval.**

**Step 4+: Generate subsequent images**

wanw decides which reference images to pass based on content:
- Want to lock face? → pick a chain image with clear face
- Want to lock outfit? → pick a full-body chain image
- Want to lock scene? → pick one with the right background

```python
result = terminal(
    f'python {SCRIPT} '
    '--step chain '
    '--model-card /path/to/model-card.jpg '
    '--ref-images "<session-dir>/chain-1.png,<session-dir>/chain-3.png" '
    '--prompt "your prompt for next image" '
    '--session-id spring_casual_001'
)
print(result["output"])
```

Send to moom, wait for approval. Repeat.

**Final step: Finalize**

When moom says enough:

```python
result = terminal(
    f'python {SCRIPT} '
    '--step chain-finalize '
    '--session-id spring_casual_001'
)
print(result["output"])
```

Deliver all finals with `MEDIA:` prefix.

### Chain Mode Reference Image Strategy

Choose references based on what you want to preserve:

| Goal | Which image to pick as reference |
|------|----------------------------------|
| Lock face | One with clear, front-facing portrait |
| Lock outfit | One with full-body shot showing complete outfit |
| Lock scene | One with the desired background/environment |
| Lock pose style | One with similar body language |
| Maximum diversity | Only pass model card, no chain images |

> [!IMPORTANT]
> Do NOT mechanically pass "the previous image". Choose references intentionally based on what needs to stay consistent. If a chain image is a close-up, it has no outfit info — don't use it to lock outfit.

---

## Directory Structure

All files are managed by the script under `~/.hermes/profiles/alice/workspace/photo-suite/`:

```
workspace/photo-suite/
├── outputs/                 # Final deliverables (by date)
│   └── YYYY-MM-DD/
│       └── <session-id>/    # e.g. colmar_001, beach_sunset_002
│           ├── final-1.png
│           ├── final-2.png
│           ├── final-3.png
│           └── final-4.png
├── tmp/                     # Intermediate files (can be cleaned)
│   └── <session-id>/
│       ├── grid.png         # Grid Mode output
│       ├── crop-1~4.png     # Grid Mode crops
│       ├── chain-1.png      # Chain Mode images
│       ├── chain-2.png
│       └── chain-N.png
└── logs/
    └── YYYY-MM-DD.log       # All API calls logged
```

## Resolution Guide

**Grid Mode:**

| Grid Resolution | Cost | Crop Size (each) | Need Upscale? |
|----------------|------|-------------------|---------------|
| 4K (default) | $0.151 | ~2K | No — good for social media |
| 2K | $0.101 | ~1K | Maybe — depends on use case |
| 1K | $0.067 | ~500px | Yes — too small without upscale |

**Chain Mode:**

| Resolution | Cost per image | Notes |
|-----------|---------------|-------|
| 2K (default) | $0.101 | Good for social media |
| 4K | $0.151 | When higher quality needed |

## Reference Documents

- **Prompt Engineering Guide**: `references/prompt-guide.md` — 详细的提示词模板、调性参考、服装/场景/光线描述技巧、手脚质量控制、超分指南。每次执行 photo-suite 前建议先加载：`skill_view("photo-suite", file_path="references/prompt-guide.md")`

## Important Notes

- All images are 9:16 portrait aspect ratio by default
- Grid Mode: default 4K, cropped images ~2K
- Chain Mode: default 2K, single images, no crop needed
- Upscale is OPTIONAL — only when moom explicitly requests higher quality
- Never bypass the script — it manages all file paths, logging, and directory structure
- Never use browser to display images — always use `MEDIA:` prefix
- Parallelizing upscale calls is your decision based on the situation
