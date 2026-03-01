"""Model loading and caching utilities."""

import subprocess
import sys
from typing import Any, Dict, Tuple

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

from . import config


def ensure_accelerate_installed() -> None:
    """Ensure accelerate package is installed for GPU device mapping.
    
    Installing at runtime can leave the module unimportable until we
    explicitly re-import it, so we do that here.
    """
    try:
        import accelerate  # noqa: F401
    except ImportError:
        print("info: 'accelerate' not found, installing it now (required for device_map)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "accelerate"])
        # Import again so that subsequent imports succeed
        import accelerate  # noqa: F401


def get_preferred_dtype() -> torch.dtype:
    """Get the preferred PyTorch dtype based on available hardware."""
    if torch.cuda.is_available():
        return torch.bfloat16 if torch.is_bf16_supported() else torch.float16
    return torch.float32


class ModelCache:
    """Cache for loaded models and processors."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, Any]] = {}
    
    def get(self, model_id: str) -> Tuple[Any, Any] | None:
        """Retrieve cached model and processor if available."""
        return self._cache.get(model_id)
    
    def set(self, model_id: str, model: Any, processor: Any) -> None:
        """Cache a model and its processor."""
        self._cache[model_id] = (model, processor)
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


# Global model cache instance
_model_cache = ModelCache()


def get_model(model_id: str) -> Tuple[Qwen3VLForConditionalGeneration, AutoProcessor]:
    """Lazy-load and cache models by ID.
    
    Loads the AutoProcessor and the model, using device_map="auto"
    and an offload_folder when CUDA is available so large models can be
    offloaded to CPU/disk as needed.
    
    Args:
        model_id: HuggingFace model ID
        
    Returns:
        Tuple of (model, processor)
        
    Raises:
        RuntimeError: If model or processor fails to load
    """
    # Check cache first
    cached = _model_cache.get(model_id)
    if cached is not None:
        return cached
    
    # Load processor
    try:
        processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=config.HF_TOKEN,
        )
    except Exception as exc:
        raise RuntimeError(f"failed to load processor for '{model_id}': {exc}")
    
    # Load model with appropriate settings
    try:
        load_kwargs: Dict[str, Any] = {
            "torch_dtype": get_preferred_dtype(),
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        if config.HF_TOKEN:
            load_kwargs["token"] = config.HF_TOKEN
        if torch.cuda.is_available():
            load_kwargs["device_map"] = "auto"
            load_kwargs["offload_folder"] = "offload"
        
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_id,
            **load_kwargs,
        )
    except Exception as exc:
        raise RuntimeError(f"failed to load model weights for '{model_id}': {exc}")
    
    model.eval()
    _model_cache.set(model_id, model, processor)
    return model, processor


def unload_model_to_cpu(model_id: str) -> None:
    """Move a cached model to CPU and update cache."""
    cached = _model_cache.get(model_id)
    if cached is not None:
        model, processor = cached
        try:
            if torch.cuda.is_available():
                model.to("cpu")
                _model_cache.set(model_id, model, processor)
                torch.cuda.empty_cache()
        except Exception:
            # Best effort only
            pass


def clear_model_cache() -> None:
    """Clear all cached models from memory."""
    _model_cache.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
