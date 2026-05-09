"""
CLIP visual embedding service
Converts clothing images into 512-dim vectors for similarity search in ChromaDB.
Model: ViT-B/32 (best balance of speed and accuracy)
"""

import io
import torch
import base64
import open_clip
from PIL import Image
from config import settings


# Load once at startup, reuse across all requests
_model, _preprocess, _tokenizer = None, None, None


def _load_model():
    """Lazy-load CLIP model on first use to avoid startup delay."""
    global _model, _preprocess, _tokenizer

    if _model is not None:
        return

    _model, _, _preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32",
        pretrained="openai"
    )
    _tokenizer = open_clip.get_tokenizer("ViT-B-32")
    _model.eval()  # Inference mode — no gradient tracking needed


def image_to_embedding(image: Image.Image) -> list[float]:
    """
    Convert a PIL Image to a 512-dimensional CLIP embedding.
    Returns a plain Python list (required by ChromaDB).
    """
    _load_model()

    # Preprocess: resize, normalize, convert to tensor
    tensor = _preprocess(image).unsqueeze(0)  # Add batch dimension

    with torch.no_grad():
        embedding = _model.encode_image(tensor)
        # Normalize to unit vector for cosine similarity
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)

    return embedding.squeeze().tolist()


def base64_to_embedding(base64_str: str) -> list[float]:
    """
    Convenience wrapper: base64 string → CLIP embedding.
    Used directly in the recommend endpoint.
    """

    # Strip data URI prefix if present
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    image_bytes = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return image_to_embedding(image)