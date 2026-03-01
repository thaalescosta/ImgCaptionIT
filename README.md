# CaptionIT

A modular Gradio application that generates LoRA-style captions for images using vision-language models.

## Features

- **Upload one or more images**
- **Pick a vision-language model from a dropdown**
- **Specify a destination folder for captions**
- **Preview images together with their captions**
- **Export individual `.txt` caption files**
- **Export a combined `all_captions.txt` file**
- **Dark theme UI** with responsive three-column layout
- **Automatic model caching** and GPU memory management
- **Fallback model selection** if primary model fails

## Setup

### 1. Install Dependencies

From the `CaptionIT` directory:

```bash
pip install -r requirements.txt
```

**Note**: PyTorch is installed separately. If `pip install -r requirements.txt` fails:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

### 2. Set HuggingFace Token (Optional)

If you're using gated models (e.g., Qwen models), set your HF token:

```powershell
# Temporary (current session only)
$env:HF_TOKEN = "your_hf_token_here"

# Permanent (requires restart)
[Environment]::SetEnvironmentVariable("HF_TOKEN", "your_hf_token_here", "User")
```

## Running the App

```bash
python app.py
```

The app will launch at `http://127.0.0.1:7860`

## Architecture

This application uses a clean **modular package architecture** organized under the `captionit/` folder for maintainability and debugging:

| Module | Purpose |
|--------|---------|
| `captionit/config.py` | Configuration, constants, and environment settings |
| `captionit/models.py` | Model loading, caching, and GPU memory management |
| `captionit/caption.py` | Caption generation and post-processing/cleaning |
| `captionit/utils.py` | Common helper functions |
| `captionit/ui.py` | Gradio interface layout and event callbacks |

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed folder organization.
See [MODULES.md](MODULES.md) for detailed API documentation of each module.

## How It Works

### Caption Generation Flow

1. **Model Loading**: Models are lazy-loaded and cached in memory
   - Uses `device_map="auto"` for GPU memory efficiency
   - Supports CPU/disk offloading for large models
   - Proper HuggingFace token authentication

2. **Image Processing**: Vision-language model generates raw caption
   - Uses system instructions derived from `caption examples/`
   - Enforces "Amateur candid iPhone" style
   - Includes configurable trigger word

3. **Caption Cleaning**: Post-processing removes unwanted patterns
   - Removes physical characteristic leaks (race, age, skin tone, hair/eye colors)
   - Removes "no content" statements
   - Enforces format requirements and keywords
   - Truncates to 1500 character limit

4. **Export**: Saves captions to `.txt` files or combined dump

### GPU Memory Management

- Models unload to CPU after processing (configurable)
- Batch processing keeps model on GPU for multiple images
- Explicit tensor cleanup and cache clearing
- Fragmentation prevention with `expandable_segments`

## Configuration

Edit `config.py` to customize:

- **Available models**: `MODEL_CHOICES`
- **Caption constraints**: `MAX_CAPTION_CHARS`, `CAPTION_KEYWORDS`
- **Generation settings**: `UNLOAD_MODEL_AFTER_EACH`, `GENERATION_USE_CACHE`
- **Trigger word**: `TRIGGER_WORD`
- **System prompt**: `IMAGE_CAPTION_INSTRUCTIONS`

## Troubleshooting

### Model Loading Fails
- Check `HF_TOKEN` environment variable is set
- Verify you have access to the model on HuggingFace
- Try with a public model first (e.g., `Qwen/Qwen2.5-VL-7B-Instruct`)

### Out of Memory
- Reduce concurrent batch processing
- Lower `MAX_CAPTION_CHARS` to reduce token generation
- Use model with fewer parameters
- Enable VRAM offloading (automatic for models >8GB)

### Captions Look Wrong
- Check system instructions in `config.py`
- Review cleaning patterns in `caption.py`
- Verify model selection and trigger word

## Recent Changes

**Major Refactoring (v2.0)**:
- ✅ Split 833-line monolithic file into 6 focused modules
- ✅ Fixed HuggingFace token passing to model loaders
- ✅ Proper GPU memory management with `ModelCache` class
- ✅ Fixed corrupted CSS code embedded in caption function
- ✅ Improved error handling and model fallback logic
- ✅ Better import organization and dependency management

See [REFACTORING.md](REFACTORING.md) for detailed changes and fixes.

## Future Enhancements

- [ ] Batch model quantization (int8, int4)
- [ ] Concurrent caption generation
- [ ] Caption history database
- [ ] New caption templates and styles
- [ ] Similarity detection for deduplication
- [ ] Advanced export formats (JSON, CSV, etc.)

