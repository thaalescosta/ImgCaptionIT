"""Gradio UI and callbacks for CaptionIT."""

import os
from pathlib import Path
from typing import Any, Dict, List

import gradio as gr
import torch

from . import caption, config, models, utils

try:
    from combine_captions import combine_captions
except ImportError:
    def combine_captions(dest_path):
        """Placeholder if combine_captions module is not available."""
        pass


def on_caption(
    files: List[str] | None,
    dest_folder: str,
    model_label: str,
    existing_items: List[Dict[str, Any]] | None,
):
    """Generate captions for uploaded images.
    
    Yields UI updates as processing progresses.
    """
    if not files:
        return (
            None,
            "Upload one or more images to generate captions.",
            existing_items or [],
            "No images to caption.",
            "",
            "",
            0,
            "",
        )
    
    model_id = config.MODEL_CHOICES.get(model_label, list(config.MODEL_CHOICES.values())[0])
    dest = utils.ensure_destination_folder(dest_folder) if dest_folder else None
    
    # Initialize items list
    items: List[Dict[str, Any]] = list(existing_items or [])
    start_idx = len(items)
    for f in files:
        image_path = f.name if hasattr(f, "name") else str(f)
        image_path = os.fspath(image_path)
        items.append({"image": image_path, "caption": "", "processed": False})
    
    # Keep model on GPU for batch processing if multiple files
    batch_keep_on_gpu = len(files) > 1
    
    # Initial UI update
    index = 0
    image, cap, fname, count, _ = utils.show_current(items, index)
    status_text = f"Starting captioning {len(files)} images..."
    yield image, cap, items, status_text, fname, count, index, utils.render_processed_list(items)
    
    # Process each file
    for idx_in_batch, f in enumerate(files):
        target_idx = start_idx + idx_in_batch
        image_path = items[target_idx]["image"]
        
        # Generate caption
        caption_text = caption.generate_caption(
            image_path, model_id, keep_model_on_gpu=batch_keep_on_gpu
        )
        
        # Try alternate models if generation failed
        if caption_text.startswith("[ERROR"):
            alt_ids = [v for k, v in config.MODEL_CHOICES.items() if v != model_id]
            for alt in alt_ids:
                alt_caption = caption.generate_caption(image_path, alt, keep_model_on_gpu=batch_keep_on_gpu)
                if not alt_caption.startswith("[ERROR"):
                    model_id = alt
                    caption_text = alt_caption
                    break
            else:
                # All attempts failed
                status_text = caption_text
                items[target_idx]["caption"] = caption_text
                items[target_idx]["processed"] = True
                yield None, caption_text, items, status_text, "", "", target_idx, utils.render_processed_list(items)
                continue
        
        items[target_idx]["caption"] = caption_text
        items[target_idx]["processed"] = True
        
        # Save caption file if destination provided
        if dest is not None:
            stem = Path(image_path).stem
            txt_path = dest / f"{stem}.txt"
            txt_path.write_text(caption_text, encoding="utf-8")
        
        status_text = f"Generated caption for {Path(image_path).name} (image {target_idx+1}/{len(items)})."
        image, cap, fname, count, _ = utils.show_current(items, target_idx)
        yield image, cap, items, status_text, fname, count, target_idx, utils.render_processed_list(items)
    
    # Finished batch - unload model if needed
    if batch_keep_on_gpu and config.UNLOAD_MODEL_AFTER_EACH and torch.cuda.is_available():
        try:
            models.unload_model_to_cpu(model_id)
        except Exception:
            pass
    
    # Final update
    status = f"Generated {len(files)} captions with model '{model_label}'."
    index = 0
    image, cap, fname, count, _ = utils.show_current(items, index)
    yield image, cap, items, status, fname, count, index, utils.render_processed_list(items)


def on_export_current(
    items: List[Dict[str, Any]] | None,
    dest_folder: str,
    index: int,
) -> str:
    """Export current caption to file."""
    if not items:
        return "No captions to export."
    if not dest_folder:
        return "Please provide a destination folder path."
    if index is None or not (0 <= index < len(items)):
        return "Invalid current image index."
    
    dest = utils.ensure_destination_folder(dest_folder)
    item = items[index]
    image_path = Path(item["image"])
    txt_path = dest / f"{image_path.stem}.txt"
    txt_path.write_text(item["caption"], encoding="utf-8")
    
    return f"Saved caption for {image_path.name} to\n{txt_path}"


def on_export_all_combined(
    items: List[Dict[str, Any]] | None,
    dest_folder: str,
) -> str:
    """Export all captions to combined file."""
    if not items:
        return "No captions to export."
    if not dest_folder:
        return "Please provide a destination folder path."
    
    dest = utils.ensure_destination_folder(dest_folder)
    
    # Ensure individual txt files exist
    for item in items:
        image_path = Path(item["image"])
        txt_path = dest / f"{image_path.stem}.txt"
        if not txt_path.exists():
            txt_path.write_text(item["caption"], encoding="utf-8")
    
    # Create combined captions file
    combine_captions(dest)
    combined_path = dest / "all_captions.txt"
    if combined_path.exists():
        return f"Exported combined captions file:\n{combined_path}"
    
    return "Tried to create combined captions file, but something went wrong."


def build_interface() -> gr.Blocks:
    """Build and return the Gradio interface."""
    default_dataset = config.DEFAULT_DATASET_PATH
    
    with gr.Blocks(elem_classes="captionit-main") as demo:
        # Header
        gr.Markdown(
            "### **CaptionIT**  \n"
            "Upload images, pick a model, and generate LoRA‑style captions."
        )
        gr.Markdown("---")
        
        # Main content: three columns
        with gr.Row():
            # Left column: controls
            with gr.Column(scale=3, elem_id="upload-column"):
                gr.Markdown("#### Controls & settings")
                
                files = gr.File(
                    label="Upload images",
                    type="filepath",
                    file_count="multiple",
                )
                
                dest_folder = gr.Textbox(
                    label="Destination folder for captions (.txt and all_captions.txt)",
                    value=str(default_dataset),
                    placeholder="e.g. C:\\ai-toolkit\\captioner\\dataset",
                )
                
                if config.MODEL_CHOICES:
                    model_dropdown = gr.Dropdown(
                        label="Select model",
                        choices=list(config.MODEL_CHOICES.keys()),
                        value=list(config.MODEL_CHOICES.keys())[0],
                        interactive=True,
                    )
                    caption_button = gr.Button(
                        "Caption it!",
                        variant="primary",
                    )
                else:
                    gr.Markdown(
                        "**No models available.**\n\n"
                        "Set `HF_TOKEN` environment variable with a valid token "
                        "and restart the app."
                    )
                    model_dropdown = gr.Dropdown(
                        label="Select model",
                        choices=[],
                        interactive=False,
                    )
                    caption_button = gr.Button(
                        "Caption it!",
                        variant="primary",
                        visible=False,
                    )
                
                status = gr.Markdown("", elem_id="captionit-status")
                processed_list = gr.HTML("", elem_id="processed-list")
            
            # Center column: image viewer
            with gr.Column(scale=4, elem_id="current-image-column"):
                current_filename = gr.Markdown("", elem_id="current-filename")
                current_image = gr.Image(type="filepath", elem_id="current-image")
                
                with gr.Row():
                    prev_btn = gr.Button("<")
                    next_btn = gr.Button(">")
                    current_count = gr.Markdown("", elem_id="current-count")
                
                with gr.Row():
                    export_current_btn = gr.Button("Export current caption")
                    export_all_btn = gr.Button("Export all captions")
            
            # Right column: caption preview
            with gr.Column(scale=3):
                captions_text = gr.Textbox(
                    label="Caption preview",
                    lines=20,
                    interactive=False,
                    elem_id="captionit-preview",
                )
        
        # Hidden state
        items_state = gr.State([])
        index_state = gr.State(0)
        
        # Event handlers
        caption_button.click(
            fn=on_caption,
            inputs=[files, dest_folder, model_dropdown, items_state],
            outputs=[current_image, captions_text, items_state, status, current_filename, current_count, index_state, processed_list],
        )
        
        prev_btn.click(
            fn=utils.prev_image,
            inputs=[items_state, index_state],
            outputs=[current_image, captions_text, current_filename, current_count, index_state],
        )
        
        next_btn.click(
            fn=utils.next_image,
            inputs=[items_state, index_state],
            outputs=[current_image, captions_text, current_filename, current_count, index_state],
        )
        
        export_current_btn.click(
            fn=on_export_current,
            inputs=[items_state, dest_folder, index_state],
            outputs=status,
        )
        
        export_all_btn.click(
            fn=on_export_all_combined,
            inputs=[items_state, dest_folder],
            outputs=status,
        )
    
    return demo
