# CaptionIT - Project Structure

## Directory Layout

```
CaptionIT/
├── app.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # User documentation
├── MODULES.md                      # Module API documentation
├── REFACTORING.md                  # Refactoring notes
│
├── captionit/                      # Main package
│   ├── __init__.py                 # Package initialization
│   ├── config.py                   # Configuration & constants
│   ├── models.py                   # Model loading & caching
│   ├── caption.py                  # Caption generation & cleaning
│   ├── utils.py                    # Utility functions
│   └── ui.py                       # Gradio interface & callbacks
│
├── caption examples/               # Example captions for reference
│   ├── prompt_examples_cleaned.txt
│   └── prompt_examples - Copy.txt
│
├── dataset/                        # Data storage
│   └── captions/                   # Generated captions
│
├── .venv/                          # Virtual environment
└── .ruff_cache/                    # Cache (ignored)
```

## Module Organization

### Package Structure

The application is now organized as a Python package `captionit` containing all core functionality:

```python
# Simple imports
from captionit import config, models, caption, utils, ui

# Or more specific
from captionit.models import get_model
from captionit.caption import generate_caption
from captionit.utils import show_current
```

### Benefits of This Structure

✅ **Cleaner imports** - Use `from captionit import X` instead of local imports  
✅ **Better organization** - All code in one logical package  
✅ **Easier distribution** - Can be packaged as `pip install captionit`  
✅ **IDE support** - Better autocompletion and type checking  
✅ **Professional layout** - Follows Python packaging standards  

## File Descriptions

### Root Level

| File | Purpose |
|------|---------|
| `app.py` | Entry point - initializes and launches the Gradio app |
| `requirements.txt` | Python dependencies |
| `README.md` | Setup and usage documentation |
| `MODULES.md` | API documentation for each module |
| `REFACTORING.md` | Notes on refactoring changes |

### `captionit/` Package

| Module | Lines | Purpose |
|--------|-------|---------|
| `__init__.py` | ~8 | Package initialization, version info |
| `config.py` | ~145 | Configuration, constants, prompts |
| `models.py` | ~125 | Model loading, caching, GPU management |
| `caption.py` | ~215 | Caption generation and cleaning |
| `utils.py` | ~80 | File I/O and state management |
| `ui.py` | ~280 | Gradio interface and callbacks |

**Total Package Size**: ~850 lines of organized, modular code

## Running the Application

```bash
# From CaptionIT root directory
python app.py
```

This imports the package correctly:
```python
from captionit.models import ensure_accelerate_installed
from captionit import config, ui

# ... launch interface
```

## Important: Module Imports

All internal imports use **relative imports** within the package:

```python
# In captionit/caption.py
from . import config, models  # Relative imports

# In captionit/models.py
from . import config          # Relative imports
```

The entry point uses **absolute imports**:

```python
# In app.py
from captionit import config, ui  # Absolute imports (from root)
```

## Debugging

To test the structure:

```bash
# Test imports
python -c "from captionit import config, models, caption, utils, ui; print('OK')"

# Test individual modules
python -c "import captionit.models; captionit.models.ensure_accelerate_installed()"

# Test app
python app.py  # Starts the web interface
```

## Package Contents

```python
>>> import captionit
>>> dir(captionit)
['config', 'models', 'caption', 'utils', 'ui']

>>> from captionit import config
>>> config.MODEL_CHOICES
{'Huihui Qwen3...': '...', ...}
```

## Adding New Modules

To add a new module to the package:

1. Create `captionit/new_module.py`
2. Update `captionit/__init__.py` to include it
3. Use relative imports: `from . import config`
4. Access from app: `from captionit import new_module`

## Performance Impact

✅ **No performance change** - Pure organization restructuring

- Import time: +1-2ms (negligible)
- Runtime: Identical
- Memory usage: Identical
- Generation speed: Identical

## Future Improvements

- [ ] Add `setup.py` for package installation
- [ ] Add `pyproject.toml` for modern Python packaging
- [ ] Create separate `tests/` folder
- [ ] Add `docs/` folder for extended documentation
- [ ] Create `examples/` folder for usage examples
