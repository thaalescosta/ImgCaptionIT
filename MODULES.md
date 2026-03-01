# CaptionIT - Module Documentation

This file documents the refactored modular structure of CaptionIT.

## Module Overview

### `app.py` - Application Entry Point
**Responsibility**: Main application entry point

- Ensures accelerate package is installed
- Initializes the Gradio interface
- Launches the web server

**Key Functions**:
- `main()` - Initializes and launches the UI

---

### `config.py` - Configuration & Constants
**Responsibility**: Centralized configuration management

Contains all:
- Model registry (`MODEL_CHOICES`)
- Caption constraints (`MAX_CAPTION_CHARS`, `CAPTION_KEYWORDS`)
- Generation settings (`GENERATION_USE_CACHE`, `UNLOAD_MODEL_AFTER_EACH`)
- UI styling (`CUSTOM_CSS`)
- System instructions (`IMAGE_CAPTION_INSTRUCTIONS`)
- PyTorch environment settings
- HuggingFace token from environment (`HF_TOKEN`)

---

### `models.py` - Model Loading & Caching
**Responsibility**: LLM model loading, caching, and GPU memory management

**Key Classes**:
- `ModelCache` - Thread-safe model and processor caching

**Key Functions**:
- `ensure_accelerate_installed()` - Installs accelerate package if needed
- `get_preferred_dtype()` - Returns optimal PyTorch dtype for hardware
- `get_model(model_id)` - Lazy-loads and caches models
- `unload_model_to_cpu(model_id)` - Moves model to CPU to free VRAM
- `clear_model_cache()` - Clears all cached models

**Features**:
- Automatic device mapping (`device_map="auto"`)
- CPU/disk offloading for large models
- GPU memory fragmentation management
- HF_TOKEN support for gated models

---

### `caption.py` - Caption Generation & Cleaning
**Responsibility**: Image captioning and caption post-processing

**Key Functions**:
- `generate_caption(image_path, model_id, keep_model_on_gpu)` - Generate caption for image
- `enforce_caption_constraints(caption)` - Ensure caption format compliance
- `clean_caption(caption)` - Remove unwanted patterns from raw caption output

**Cleaning Rules**:
- Removes no-content statements ("No explicit nudity", etc.)
- Removes physical characteristic leaks (hair colors, eye colors, skin tones)
- Removes non-ASCII characters
- Cleans up regex artifacts (double spaces, punctuation issues)
- Enforces trigger word and keywords presence
- Truncates to max length

---

### `utils.py` - Utility Functions
**Responsibility**: Common helper functions for file I/O and UI state

**Key Functions**:
- `ensure_destination_folder(path_str)` - Create destination folder if needed
- `show_current(items, index)` - Get UI data for image at index
- `prev_image()` - Navigate to previous image
- `next_image()` - Navigate to next image
- `format_captions_summary(items)` - Format captions for display
- `render_processed_list(items)` - Render HTML status list

---

### `ui.py` - Gradio Interface & Callbacks
**Responsibility**: Web interface layout and event handlers

**Key Functions**:
- `build_interface()` - Constructs the Gradio block layout
- `on_caption()` - Batch caption generation callback
- `on_export_current()` - Export single caption
- `on_export_all_combined()` - Export all captions with combine script

**Features**:
- Three-column layout (controls, image viewer, caption preview)
- Real-time progress updates via generators
- Model fallback logic (tries alternate models if primary fails)
- Batch processing optimization (keeps model on GPU for multiple images)

---

## Data Flow

```
┌─────────────┐
│   app.py    │ Entry point
└──────┬──────┘
       │
       └─→ ui.build_interface()
           │
           ├─→ config: Load UI CSS, model choices
           │
           └─→ Event handlers:
               
               on_caption():
               ├─→ For each image:
               │   └─→ caption.generate_caption()
               │       ├─→ models.get_model(model_id)
               │       │   ├─→ Load from cache or fetch from HF
               │       │   └─→ Cache for reuse
               │       ├─→ Run model inference
               │       └─→ caption.clean_caption()
               │
               └─→ Export callbacks:
                   └─→ utils functions + combine_captions
```

---

## Environment Variables

- `HF_TOKEN` - HuggingFace API token for gated model access
- `PYTORCH_CUDA_ALLOC_CONF` - Set automatically to `expandable_segments:True` for better GPU memory management

---

## Error Handling

### Model Loading Errors
- If model fails to load, caption generation returns error message with details
- UI attempts to load alternate models before giving up

### Tensor Cleanup
- After generation, all temporary tensors are explicitly deleted
- `torch.cuda.empty_cache()` called to prevent memory fragmentation

### File I/O Errors
- Destination folders are automatically created with `mkdir(parents=True)`
- File write errors are propagated to user via status messages

---

## Debugging Tips

1. **Check imports**: Run `python -c "import config; import models; import caption; import utils; import ui"`
2. **Verify HF_TOKEN**: Check `echo $env:HF_TOKEN` in PowerShell
3. **Model cache**: Models persist in memory - restart app to clear
4. **GPU memory**: Use `torch.cuda.mem_get_info()` to check available VRAM
5. **Logs**: Gradio captures stdout; watch terminal for generation details

---

## Future Improvements

- [ ] Add database for caption history
- [ ] Implement batch export directly without combine_captions dependency
- [ ] Add caption template system for different prompt styles
- [ ] Add model quantization options (int8, int4)
- [ ] Implement concurrent caption generation
- [ ] Add caption similarity/deduplication checks
