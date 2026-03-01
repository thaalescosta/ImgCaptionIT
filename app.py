#!/usr/bin/env python3
"""CaptionIT - Generate LoRA-style captions for images.

A Gradio application for generating captions from images using vision-language models,
with support for multiple models and destination folders.
"""

# Ensure accelerate is available before any torch imports
from captionit.models import ensure_accelerate_installed

ensure_accelerate_installed()

from captionit import config, ui


def main():
    """Run the CaptionIT application."""
    app = ui.build_interface()
    
    # Launch with theme and CSS
    app.launch(
        theme="soft",
        css=config.CUSTOM_CSS,
    )


if __name__ == "__main__":
    main()
