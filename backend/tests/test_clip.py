"""
CLIP service test — verifies model loads and produces correct embeddings.
Usage: pytest tests/test_clip.py -v
"""

import pytest
import base64
import io
import numpy as np
from PIL import Image


def _make_dummy_base64(color=(255, 0, 0), size=(224, 224)) -> str:
    """Create a solid-color dummy image as base64 for testing."""
    img = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class TestCLIPService:

    def test_model_loads(self):
        """CLIP model should load without errors."""
        from services.clip_service import _load_model
        _load_model()
        from services.clip_service import _model
        assert _model is not None

    def test_embedding_dimension(self):
        """CLIP ViT-B/32 must produce 512-dimensional embeddings."""
        from services.clip_service import image_to_embedding
        img = Image.new("RGB", (224, 224), color=(128, 128, 128))
        embedding = image_to_embedding(img)

        assert isinstance(embedding, list), "Embedding must be a list"
        assert len(embedding) == 512, f"Expected 512 dims, got {len(embedding)}"

    def test_embedding_is_normalized(self):
        """Embeddings must be unit vectors (norm ≈ 1.0) for cosine similarity."""
        from services.clip_service import image_to_embedding
        img = Image.new("RGB", (224, 224), color=(0, 128, 255))
        embedding = image_to_embedding(img)

        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-5, f"Embedding not normalized, norm={norm:.6f}"

    def test_base64_input(self):
        """base64_to_embedding() must accept base64 strings from frontend."""
        from services.clip_service import base64_to_embedding
        b64 = _make_dummy_base64(color=(0, 255, 0))
        embedding = base64_to_embedding(b64)

        assert len(embedding) == 512

    def test_base64_with_data_uri_prefix(self):
        """Must handle data URI prefix (data:image/jpeg;base64,...) from browser."""
        from services.clip_service import base64_to_embedding
        b64 = _make_dummy_base64()
        b64_with_prefix = f"data:image/jpeg;base64,{b64}"
        embedding = base64_to_embedding(b64_with_prefix)

        assert len(embedding) == 512

    def test_different_images_produce_different_embeddings(self):
        """Two different images must not produce identical embeddings."""
        from services.clip_service import image_to_embedding
        img_red  = Image.new("RGB", (224, 224), color=(255, 0, 0))
        img_blue = Image.new("RGB", (224, 224), color=(0, 0, 255))

        emb_red  = np.array(image_to_embedding(img_red))
        emb_blue = np.array(image_to_embedding(img_blue))

        cosine_sim = np.dot(emb_red, emb_blue)
        assert cosine_sim < 0.999, "Different images should not be identical"