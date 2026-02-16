"""
Screenshot processing and annotation utilities.

Handles encoding, resizing, and optional annotation of screenshots
before they are sent to AI models or embedded in reports.
"""

import base64
import io
from pathlib import Path
from typing import Optional

from PIL import Image


def screenshot_to_base64(screenshot_bytes: bytes) -> str:
    """Convert raw screenshot bytes to a base64-encoded string."""
    return base64.b64encode(screenshot_bytes).decode("utf-8")


def base64_to_bytes(b64_string: str) -> bytes:
    """Decode a base64 string back to bytes."""
    return base64.b64decode(b64_string)


def resize_screenshot(
    screenshot_bytes: bytes,
    max_width: int = 1280,
    max_height: int = 1024,
    quality: int = 85,
) -> bytes:
    """
    Resize a screenshot to fit within max dimensions while preserving
    aspect ratio. Returns JPEG bytes for smaller payload.
    """
    img = Image.open(io.BytesIO(screenshot_bytes))

    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img_rgb = img.convert("RGB")
    img_rgb.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


def save_screenshot(
    screenshot_bytes: bytes,
    output_dir: str,
    filename: str,
) -> str:
    """Save screenshot bytes to disk. Returns the saved file path."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_path = out_path / filename
    file_path.write_bytes(screenshot_bytes)
    return str(file_path)


def prepare_for_ai(
    screenshot_bytes: bytes,
    max_width: int = 1280,
    max_height: int = 1024,
) -> str:
    """Resize and encode a screenshot for AI model consumption."""
    resized = resize_screenshot(screenshot_bytes, max_width, max_height)
    return screenshot_to_base64(resized)
