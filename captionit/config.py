"""Configuration and constants for CaptionIT."""

from pathlib import Path
from typing import Dict
import os

# Project root (one level up from this package)
ROOT_DIR = Path(__file__).resolve().parents[1]

# Model registry
MODEL_CHOICES: Dict[str, str] = {
    "Huihui Qwen3 VL 4B (abliterated)": "Huihui/Qwen3-VL-4B-Abliterated",
    "Huihui Qwen3 VL 8B (abliterated)": "Huihui/Qwen3-VL-8B-Abliterated",
    "Qwen2.5 VL 7B Instruct": "Qwen/Qwen2.5-VL-7B-Instruct",
}

# Model loading settings
UNLOAD_MODEL_AFTER_EACH = True
GENERATION_USE_CACHE = False

# Trigger word for captions
TRIGGER_WORD = "Lo1r4"

# Default dataset path
DEFAULT_DATASET_PATH = ROOT_DIR / "dataset" / "captions"

# Caption constraints
MAX_CAPTION_CHARS = 1500
CAPTION_KEYWORDS = "Sharp subject and background. High angle view, medium shot, visible grain and digital artifacts."

# HuggingFace token
HF_TOKEN = os.environ.get("HF_TOKEN")

# CUDA settings
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

# Instruction prompt for caption generation
IMAGE_CAPTION_INSTRUCTIONS = """
You are an expert caption generator for Z-Image Turbo. Your job is to write a
prompt that, when fed to a stable model enhanced with the user's custom
LoRA, will faithfully reproduce the supplied image. Produce a single, plain
English paragraph (one paragraph, up to 1500 characters) that matches the
"Amateur candid iPhone" style in the examples. Requirements:

- Be as detailed and descriptive as possible about even the smallest details, while following the formatting and content rules below. The more detailed the caption, the better.
- ALWAYS begin the prompt with the literal phrase: Amateur candid iPhone
- ALWAYS include the trigger token Lo1r4 somewhere immediately after the
    initial phrase (examples: "Amateur candid iPhone selfie of Lo1r4",
    "Amateur candid iPhone mirror selfie of Lo1r4", "Amateur candid iPhone
    photograph of Lo1r4").
- DO NOT describe or mention any intrinsic physical characteristics such as
    race, age, skin colour/tone, hair colour, eye colour, facial feature
    descriptors, body proportions, or other identity attributes. Only describe
    variable, situational, visible details, mood, and context.
- Keep the text concrete and observational. No metaphors, no mood
    interpretation, and no filler. Use clear camera/photography language.
- Follow a compact order when possible: SHOT & FRAMING; HAIRSTYLE (length/style
    but NOT colour); EXPRESSION; POSE; CLOTHING/coverage (or "nude" if none);
    EXPLICIT CONTENT (explicitly and plainly, if present); BACKGROUND/SETTING;
    LIGHTING.
- When describing lighting, avoid subjective terms like "soft" or "harsh" and instead describe the light source, colors, direction, and quality (e.g. "natural light from window on the left", "warm incandescent overhead light", "cool LED light illuminating from the right").
- End the caption with the camera keywords (exactly):
    Sharp subject and background. High angle view, medium shot, visible grain and digital artifacts.
- Ignore any watermarks that may be present in the image and do not mention them in the caption.

Do not include any non-ASCII characters. Produce the caption only (no
explanatory text, no lists, no bullet points)."""

# Gradio UI CSS
CUSTOM_CSS = """
:root {
  --background-fill-primary: #000000;
  --body-background-fill: #000000;
  --block-background-fill: #050505;
  --border-color-primary: #333333;
  --color-accent: #ffffff;
  --text-color: #ffffff;
}

.gradio-container {
  background-color: #000000 !important;
  color: #ffffff !important;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text",
    "Segoe UI", sans-serif;
}

.captionit-main {
  min-height: 100vh;
  padding: 0 !important;
}

#captionit-gallery {
  background: radial-gradient(circle at 30% 20%, #222 0, #000 55%);
}

#captionit-arrow {
  font-size: 3.2rem;
  text-align: center;
  color: #ffffff;
  opacity: 0.9;
  padding-top: 3rem;
}

#captionit-model-selector {
  width: 100%;
}

#captionit-status {
  color: #aaaaaa;
}

#upload-column {
  padding: 1rem;
  border-right: 1px solid #333333;
}

#current-image-column img {
  max-width: 100%;
  border: 1px solid #444;
}

#current-filename {
  text-align: center;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

#current-count {
  margin-left: 1rem;
  align-self: center;
}

#captionit-preview textarea {
  background-color: #111 !important;
  color: #fff !important;
}
"""
