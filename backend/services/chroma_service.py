"""
ChromaDB vector search service
Stores and retrieves fashion outfit embeddings.
Collection is pre-populated via data/embed_dataset.ipynb.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings


# Persistent client — data survives restarts
_client = None
_collection = None

COLLECTION_NAME = "fashion_outfits"


def _get_collection():
    """
    Lazy-initialize ChromaDB client and collection.
    Called on first search request, not at startup.
    """
    global _client, _collection

    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(
        path=settings.CHROMA_DB_PATH,
        settings=ChromaSettings(anonymized_telemetry=False)
    )

    # Get or create collection
    # cosine distance is best for normalized CLIP embeddings
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    return _collection


def search_similar_outfits(embedding: list[float], n_results: int = 20, category_filter: str | None = None) -> list[dict]:
    """
    Find the most visually similar outfits in ChromaDB.

    Args:
        embedding:       512-dim CLIP vector of the query image
        n_results:       Number of results to return (default 20, top 10 sent to Gemini)
        category_filter: Optional — filter by clothing category (e.g. "top", "dress")

    Returns:
        List of metadata dicts, each containing:
        { id, description, category, style, color, source }
    """
    collection = _get_collection()

    # Return empty list if collection has no data yet
    if collection.count() == 0:
        return []

    # Build optional where clause for metadata filtering
    where = {"category": category_filter} if category_filter else None

    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(n_results, collection.count()),
        where=where,
        include=["metadatas", "distances"]
    )

    # Flatten results into a simple list of dicts
    outfits = []
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for metadata, distance in zip(metadatas, distances):
        outfits.append({
            **metadata,
            "similarity_score": round(1 - distance, 4)  # Convert distance to similarity
        })

    return outfits


def add_outfit(outfit_id: str, embedding: list[float], metadata: dict) -> None:
    """
    Add a single outfit embedding to ChromaDB.
    Used by embed_dataset.ipynb during the data pipeline.

    Metadata should include:
    { description, category, style, color, pattern, source, dataset }
    """
    collection = _get_collection()
    collection.add(
        ids=[outfit_id],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def get_collection_stats() -> dict:
    """
    Return basic stats about the collection.
    Useful for debugging and health checks.
    """
    collection = _get_collection()
    return {
        "collection": COLLECTION_NAME,
        "total_items": collection.count(),
        "db_path": settings.CHROMA_DB_PATH,
    }

def get_or_create_collection(collection_name: str):
    """
    Get or create a named ChromaDB collection.
    Used by Stil DNA to create per-user collections.
    """
    global _client

    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

    return _client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )