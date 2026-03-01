"""Caption generation and cleaning utilities."""

import gc
import re
from pathlib import Path

import torch

from . import config, models


def generate_caption(image_path: str, model_id: str, keep_model_on_gpu: bool = False) -> str:
    """Generate a caption for an image.
    
    Args:
        image_path: Path to the image file
        model_id: HuggingFace model ID
        keep_model_on_gpu: If True, keep model on GPU after generation
        
    Returns:
        Generated caption string, or error message if generation fails
    """
    # Load the model/processor
    try:
        model, processor = models.get_model(model_id)
    except Exception as exc:
        return f"[ERROR loading model: {exc}]"
    
    # Ensure we have a string path, not a Path object
    if isinstance(image_path, Path):
        image = str(image_path)
    else:
        image = image_path
    
    # Build chat messages for the vision-language model
    messages = [
        {"role": "system", "content": config.IMAGE_CAPTION_INSTRUCTIONS},
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {
                    "type": "text",
                    "text": "Generate a single training caption for this image following the system instructions exactly.",
                },
            ],
        },
    ]
    
    # Prepare inputs
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt").to(model.device)
    
    # Generate caption
    try:
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.12,
                top_p=0.85,
                repetition_penalty=1.1,
                use_cache=config.GENERATION_USE_CACHE,
            )
        
        generated = output_ids[:, inputs["input_ids"].shape[1] :]
        raw = processor.decode(generated[0], skip_special_tokens=True).strip()
    except Exception as exc:
        return f"[ERROR generating caption: {exc}]"
    finally:
        # Clean up temporary tensors
        try:
            del inputs, output_ids, generated
        except (NameError, UnboundLocalError):
            pass
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # Clean caption
    caption = clean_caption(raw)
    
    # Optionally unload model from GPU
    if config.UNLOAD_MODEL_AFTER_EACH and torch.cuda.is_available() and not keep_model_on_gpu:
        models.unload_model_to_cpu(model_id)
    
    # Post-process: ensure trigger word and keywords
    caption = enforce_caption_constraints(caption)
    
    return caption


def enforce_caption_constraints(caption: str) -> str:
    """Ensure caption has required structure and keywords.
    
    - Starts with "Amateur candid iPhone"
    - Contains trigger word
    - Ends with camera keywords
    - Does not exceed max length
    """
    # Ensure starts with required phrase and contains trigger word
    if caption.lower().startswith("amateur candid iphone"):
        if config.TRIGGER_WORD not in caption:
            caption = caption.replace(
                "Amateur candid iPhone",
                f"Amateur candid iPhone {config.TRIGGER_WORD}",
                1,
            )
    else:
        caption = f"Amateur candid iPhone {config.TRIGGER_WORD} {caption}"
    
    # Ensure keywords at end (do not duplicate)
    if config.CAPTION_KEYWORDS not in caption:
        # Make room for keywords if necessary
        allowed_body = config.MAX_CAPTION_CHARS - len(config.CAPTION_KEYWORDS) - 1
        body = caption
        if len(body) > allowed_body:
            body = body[:allowed_body].rstrip()
        caption = f"{body} {config.CAPTION_KEYWORDS}".strip()
    else:
        # If already contains keywords, just truncate to max length
        if len(caption) > config.MAX_CAPTION_CHARS:
            caption = caption[:config.MAX_CAPTION_CHARS].rstrip()
    
    return caption.strip()


def clean_caption(caption: str) -> str:
    """Remove unwanted patterns from caption."""
    # Remove explicit no-content statements
    patterns_to_remove = [
        r"No explicit nudity[^.]*\.",
        r"No explicit content[^.]*\.",
        r"No explicit sexual acts[^.]*\.",
        r"No nudity[^.]*\.",
        r"No visible nudity[^.]*\.",
        r"No sexual content[^.]*\.",
        r"No explicit[^.]*\.",
        # Absence of face
        r"\bface unseen[^,\.]*[,\.]?",
        r"\bface not visible[^,\.]*[,\.]?",
        r"\bface (is |turned )?away[^,\.]*[,\.]?",
        # Out-of-frame limbs
        r"\b\w+ (arm|hand|leg|foot|feet) out of frame[^,\.]*[,\.]?",
        r"\b(arms?|hands?|legs?|feet|foot) out of frame[^,\.]*[,\.]?",
        r"\bholds? (an? )?object out of frame[^,\.]*[,\.]?",
        r"\bholding (an? )?object out of frame[^,\.]*[,\.]?",
        r"\b(holding|grasping|carrying) [^,\.]+ out of frame[^,\.]*[,\.]?",
        r"out of frame",
        # Absence clothing language
        r"\bno (clothing|garments?|fabric|top|bottoms?) covering[^,\.]*[,\.]?",
        r"\bno (clothing|garments?) (on|visible)[^,\.]*[,\.]?",
        r"\bnothing covering[^,\.]*[,\.]?",
        r"\bno skin visible[^,\.]*[,\.]?",
        r"no skin visible beneath[^,\.]*[,\.]?",
        # Concealment language
        r"\bgenitals? (completely |fully )?(concealed|hidden|covered|exposed)[^,\.]*[,\.]?",
        r"\bpubic (area|mound|region) (fully |completely )?exposed[^,\.]*[,\.]?",
        # Negative descriptions
        r"\bdoes not (reveal|show|expose|display)[^,\.]*[,\.]?",
        r"\bnot (visible|shown|present|revealed)[^,\.]*[,\.]?",
        # Vague terms
        r"\brevealing cleavage[^,\.]*",
        r"\bbreasts? naturally positioned[^,\.]*[,\.]?",
        r"\bnaturally positioned[^,\.]*[,\.]?",
        # Skin quality (implies skin tone)
        r"\b(smooth|flawless|clear|glowing|luminous) skin[^,\.]*[,\.]?",
        r"\bsmooth skin illuminated[^,\.]*[,\.]?",
        # Gradient backgrounds
        r"gradient background",
        r"gradient backdrop",
    ]
    
    for pattern in patterns_to_remove:
        caption = re.sub(pattern, "", caption, flags=re.IGNORECASE)
    
    # Remove hair color leaks
    hair_color_patterns = [
        r"\b(dark\s+)?blonde\s+(hair\b)?",
        r"\bbrunette\b",
        r"\b(dark\s+brown|light\s+brown|medium\s+brown)\s+hair\b",
        r"\bbrown\s+hair\b",
        r"\bblack\s+hair\b",
        r"\bred\s+hair\b",
        r"\bauburn\s+hair\b",
        r"\bgolden\s+hair\b",
        r"\bsilver\s+hair\b",
        r"\bgr[ae]y\s+hair\b",
        r"\bdark\s+hair\b",
        r"\blight\s+hair\b",
        r"\bstrawberry\s+blonde\b",
        r"\bplatinum\s+(blonde\s+)?hair\b",
        r"\bchestnut\s+hair\b",
        r"\bcopper\s+hair\b",
    ]
    
    for pattern in hair_color_patterns:
        caption = re.sub(pattern, "", caption, flags=re.IGNORECASE)
    
    # Remove eye color leaks
    eye_color_patterns = [
        r"\b(blue|green|brown|hazel|gray|grey|amber|dark|light)\s+eyes?\b",
        r"\bbright\s+(blue|green|brown|hazel)\b",
        r"\beyes?\s+(are\s+)?(blue|green|brown|hazel|gray|grey|amber)\b",
    ]
    
    for pattern in eye_color_patterns:
        caption = re.sub(pattern, "", caption, flags=re.IGNORECASE)
    
    # Remove skin tone leaks
    skin_tone_patterns = [
        r"\b(fair|pale|light|medium|olive|tan|tanned|dark|deep|warm|cool)\s+(skin|complexion)\b",
        r"\b(fair|pale|light|medium|olive|tan|tanned|dark|deep)\s+toned\b",
    ]
    
    for pattern in skin_tone_patterns:
        caption = re.sub(pattern, "", caption, flags=re.IGNORECASE)
    
    # Remove non-ASCII characters
    caption = re.sub(r"[^\x00-\x7F]+", "", caption)
    
    # Clean up artifacts from removals
    caption = re.sub(r"[ \t]+", " ", caption)  # Collapse spaces
    caption = re.sub(r" ,", ",", caption)  # Remove space before comma
    caption = re.sub(r",\s*,+", ",", caption)  # Remove double commas
    caption = re.sub(r"\.\s*\.", ".", caption)  # Remove double periods
    caption = re.sub(r",\s*\.", ".", caption)  # Remove comma before period
    caption = re.sub(r"\s+\.\s*", ". ", caption)  # Fix space before period
    caption = re.sub(r"\.\s+,", ".", caption)  # Fix period then comma
    caption = re.sub(r"^[,\s]+", "", caption)  # Remove leading punctuation
    caption = caption.strip()
    
    return caption
