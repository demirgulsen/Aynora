"""
ChromaDB service test — compatible with ChromaDB 1.5+
Usage: pytest tests/test_chroma.py -v
"""

import pytest
import numpy as np
import uuid
import os
import shutil
import time

TEST_CHROMA_PATH = "./test_chroma_db"


@pytest.fixture(autouse=True)
def clean_test_db(monkeypatch, tmp_path):
    """
    - Uses pytest's tmp_path for a truly isolated temp directory per test
    - Overrides CHROMA_DB_PATH via monkeypatch
    - Resets the singleton before and after each test
    - ChromaDB 1.5+ doesn't need explicit client.stop()
    """
    test_db = str(tmp_path / "chroma_db")
    monkeypatch.setenv("CHROMA_DB_PATH", test_db)

    # Patch settings directly since it's already loaded
    import services.chroma_service as cs
    monkeypatch.setattr("services.chroma_service._client", None)
    monkeypatch.setattr("services.chroma_service._collection", None)

    # Also patch the settings object so _get_collection reads correct path
    from config import settings
    monkeypatch.setattr(settings, "CHROMA_DB_PATH", test_db)

    yield

    # Reset singleton after test
    cs._client = None
    cs._collection = None


def _random_embedding(dim=512) -> list[float]:
    vec = np.random.rand(dim).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def _sample_metadata(category="top", source="test") -> dict:
    return {
        "source": source,
        "category": category,
        "filename": f"{uuid.uuid4().hex[:8]}.jpg",
        "description": f"{category} clothing item from {source}",
    }


class TestChromaService:

    def test_collection_created(self):
        """Collection should be created on first access."""
        from services.chroma_service import _get_collection
        collection = _get_collection()
        assert collection is not None
        assert collection.name == "fashion_outfits"

    def test_empty_collection_returns_empty_list(self):
        """search_similar_outfits() must return [] when collection is empty."""
        from services.chroma_service import search_similar_outfits
        results = search_similar_outfits(_random_embedding(), n_results=5)
        assert results == []

    def test_add_and_search(self):
        """Added items must be retrievable via similarity search."""
        from services.chroma_service import add_outfit, search_similar_outfits

        for _ in range(5):
            add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata())

        results = search_similar_outfits(_random_embedding(), n_results=3)
        assert len(results) == 3

    def test_search_returns_correct_fields(self):
        """Each result must contain required metadata fields."""
        from services.chroma_service import add_outfit, search_similar_outfits

        add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata(category="dress"))
        results = search_similar_outfits(_random_embedding(), n_results=1)

        assert len(results) == 1
        item = results[0]
        for field in ["category", "source", "description", "similarity_score"]:
            assert field in item, f"Missing field: {field}"

    def test_similarity_score_range(self):
        """Similarity scores must be between 0 and 1."""
        from services.chroma_service import add_outfit, search_similar_outfits

        for _ in range(3):
            add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata())

        results = search_similar_outfits(_random_embedding(), n_results=3)
        for item in results:
            assert 0.0 <= item["similarity_score"] <= 1.0, \
                f"Score out of range: {item['similarity_score']}"

    def test_category_filter(self):
        """search_similar_outfits() must filter by category when provided."""
        from services.chroma_service import add_outfit, search_similar_outfits

        for _ in range(3):
            add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata(category="top"))
        for _ in range(3):
            add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata(category="bottom"))

        results = search_similar_outfits(_random_embedding(), n_results=10, category_filter="top")
        assert all(r["category"] == "top" for r in results), \
            "Category filter returned wrong categories"

    def test_get_collection_stats(self):
        """get_collection_stats() must return correct count and path."""
        from services.chroma_service import add_outfit, get_collection_stats

        for _ in range(4):
            add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata())

        stats = get_collection_stats()
        assert stats["total_items"] == 4, f"Expected 4, got {stats['total_items']}"
        assert stats["collection"] == "fashion_outfits"
        assert "db_path" in stats

    def test_similar_items_rank_higher(self):
        """Same vector queried back should be the top result."""
        from services.chroma_service import add_outfit, search_similar_outfits

        for _ in range(5):
            add_outfit(str(uuid.uuid4()), _random_embedding(), _sample_metadata())

        known_vec = _random_embedding()
        add_outfit(str(uuid.uuid4()), known_vec, _sample_metadata(category="dress", source="known"))

        results = search_similar_outfits(known_vec, n_results=6)

        top = results[0]
        assert top["source"] == "known", \
            f"Expected 'known' as top result, got '{top['source']}'"
        assert top["similarity_score"] > 0.99, \
            f"Same vector should score ≈ 1.0, got {top['similarity_score']}"