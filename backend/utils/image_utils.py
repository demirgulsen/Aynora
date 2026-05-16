"""
Image processing helpers
Handles validation, resizing, format conversion and temporary storage of uploaded images.
"""

import base64
import io
import os
import uuid
import hashlib
from PIL import Image

# Supported input formats
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# Max dimensions before resizing (CLIP works best with 224x224,
# but we keep a larger size for Gemini Vision quality)
MAX_SIZE = (1024, 1024)

# Temporary upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def decode_base64_image(base64_str: str) -> Image.Image:
    """
    Decode a base64 string (with or without data URI prefix) to a PIL Image.
    Raises ValueError if the format is not supported.
    """
    # Strip data URI prefix if present: "data:image/jpeg;base64,..."
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    image_bytes = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_bytes))

    if image.format not in ALLOWED_FORMATS:
        raise ValueError(
            f"Unsupported image format: {image.format}. "
            f"Allowed formats: {', '.join(ALLOWED_FORMATS)}"
        )

    return image


def resize_image(image: Image.Image, max_size: tuple = MAX_SIZE) -> Image.Image:
    """
    Resize image to fit within max_size while preserving aspect ratio.
    Does nothing if the image is already smaller.
    """
    image.thumbnail(max_size, Image.LANCZOS)
    return image


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """
    Convert image to RGB mode.
    Required for CLIP (does not support RGBA or palette images).
    """
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """
    Convert a PIL Image back to a base64 string.
    Useful for passing processed images to Gemini Vision.
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


# utils/image_utils.py — save_upload fonksiyonunu güncelle



def save_upload(image: Image.Image, prefix: str = "upload") -> str:
    """
    Save image to static/uploads/ for debugging.
    Skips saving if identical image already exists (hash check).
    """
    # Hash based on image content — same image = same hash
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG")
    img_hash  = hashlib.md5(buffer.getvalue()).hexdigest()[:12]
    filename  = f"{prefix}_{img_hash}.jpg"
    filepath  = os.path.join(UPLOAD_DIR, filename)

    # Skip if already saved
    if os.path.exists(filepath):
        return filepath

    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    return filepath


def process_uploaded_image(base64_str: str, save: bool = False) -> tuple[Image.Image, str]:
    """
    Full processing pipeline for an uploaded image:
    1. Decode base64
    2. Validate format
    3. Resize if needed
    4. Convert to RGB
    5. Optionally save to disk for debugging

    Returns: (processed PIL Image, base64 string of processed image)
    """
    image = decode_base64_image(base64_str)
    image = resize_image(image)
    image = convert_to_rgb(image)

    if save:
        save_upload(image)

    processed_base64 = image_to_base64(image)
    return image, processed_base64