"""Utility functions for CaptionIT."""

from pathlib import Path
from typing import Any, Dict, List, Tuple


def ensure_destination_folder(path_str: str) -> Path:
    """Create destination folder if it doesn't exist.
    
    Args:
        path_str: Path to the folder
        
    Returns:
        Path object pointing to the created folder
    """
    base = Path(path_str).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base


def show_current(
    items: List[Dict[str, Any]], index: int
) -> Tuple[Any, str, str, str, int]:
    """Get UI data for the caption at the given index.
    
    Returns a tuple: (image_path_or_None, caption, filename, count_str, index).
    """
    if not items:
        # Gradio treats empty string as a path and tries to open it, leading to
        # permission errors. Use None to indicate no image.
        return None, "", "", "", 0
    
    index = max(0, min(index, len(items) - 1))
    item = items[index]
    image = item["image"]
    cap = item["caption"]
    fname = Path(image).name
    count = f"{index+1}/{len(items)}"
    return image, cap, fname, count, index


def prev_image(items: List[Dict[str, Any]], index: int) -> Tuple[Any, str, str, str, int]:
    """Navigate to previous image."""
    new_index = max(0, index - 1) if items else 0
    return show_current(items, new_index)


def next_image(items: List[Dict[str, Any]], index: int) -> Tuple[Any, str, str, str, int]:
    """Navigate to next image."""
    new_index = min(len(items) - 1, index + 1) if items else 0
    return show_current(items, new_index)


def format_captions_summary(items: List[Dict[str, Any]]) -> str:
    """Format captions for summary display."""
    if not items:
        return "No captions yet."
    
    lines: List[str] = []
    for idx, item in enumerate(items, 1):
        name = Path(item["image"]).name
        lines.append(f"{idx:02d}. {name}\n{item['caption']}\n")
    
    return "\n".join(lines).strip()


def render_processed_list(items: List[Dict[str, Any]]) -> str:
    """Render HTML for processed/unprocessed status list."""
    if not items:
        return '<div class="proc-item">No images.</div>'
    
    parts: List[str] = []
    for i, item in enumerate(items):
        name = Path(item["image"]).name
        processed = bool(item.get("processed"))
        badge_class = "processed" if processed else "unprocessed"
        parts.append(
            f'<div class="proc-item"><span class="proc-badge {badge_class}"></span>'
            f'<span class="proc-fname">{i+1:02d}. {name}</span></div>'
        )
    
    return "".join(parts)
