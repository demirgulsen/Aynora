"""
cache_service.py — Semantic caching with Upstash Redis
Caches Gemini responses for similar queries to reduce API calls and latency.

How it works:
1. Convert request to embedding (sentence-transformers)
2. Check Redis for similar cached response (cosine similarity > threshold)
3. HIT  → return cached result instantly (~50ms)
4. MISS → call Gemini, cache the result with TTL

Strategy:
- Cache 20 outfits per unique semantic query
- Return 5 random outfits each time → user sees variety
- TTL: 24 hours
- Similarity threshold: 0.90
"""
import random
import json
import hashlib
import logging
import numpy as np
from upstash_redis import Redis
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)

# Similarity threshold — above this score, cache hit is returned
SIMILARITY_THRESHOLD = 0.90
# Cache TTL in seconds (24 hours)
CACHE_TTL = 86400
# Max cached entries to scan for similarity (keep low for speed)
MAX_SCAN_KEYS = 200
# Store N outfits per query
CACHE_POOL_SIZE = 20
# Return N random outfits per request
SERVE_SIZE = 5

# ── Lazy singletons ───────────────────────────────────────────
_redis:  Redis | None = None
_model:  SentenceTransformer | None = None


def _get_redis() -> Redis | None:
    """Lazy-initialize Upstash Redis client."""
    global _redis
    if _redis is not None:
        return _redis
    url   = getattr(settings, "UPSTASH_REDIS_REST_URL",   None)
    token = getattr(settings, "UPSTASH_REDIS_REST_TOKEN", None)
    if not url or not token:
        logger.warning("Upstash Redis not configured — caching disabled")
        return None
    _redis = Redis(url=url, token=token)
    return _redis


def _get_model() -> SentenceTransformer:
    """Lazy-initialize sentence-transformers model."""
    global _model
    if _model is None:
        # Lightweight multilingual model — supports Turkish
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def _build_cache_key(embedding: list[float]) -> str:
    """Create a short hash key from embedding for Redis storage."""
    raw = json.dumps(embedding[:16])   # Use first 16 dims for key — fast
    return f"aynora:emb:{hashlib.md5(raw.encode()).hexdigest()}"


def _embed_query(text: str) -> list[float]:
    """Convert query text to embedding vector."""
    model = _get_model()
    vec   = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two normalized vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.dot(va, vb))


def _query_text(params: dict) -> str:
    """
    Build a single string from request params for embedding.
    Captures the semantic meaning of the request.
    """
    parts = [
        params.get("message", ""),
        params.get("concept",          ""),
        params.get("color_preference", ""),
        params.get("gender",           ""),
        params.get("weather",          ""),
        params.get("size",             ""),
        params.get("additional_notes", "") or "",
    ]
    return " ".join(filter(None, parts)).strip()


async def get_cached(params: dict) -> dict | None:
    """
    Look up a cached response for semantically similar params.
    Returns cached result dict or None on miss.
    """
    redis = _get_redis()
    if redis is None:
        return None

    try:
        query  = _query_text(params)
        if not query:
            return None

        q_emb  = _embed_query(query)

        # Scan recent cache keys
        keys = redis.keys("aynora:emb:*")
        if not keys:
            return None

        # Check similarity against cached embeddings
        for key in keys[:MAX_SCAN_KEYS]:
            entry_raw = redis.get(key)
            if not entry_raw:
                continue

            entry = json.loads(entry_raw)
            cached_emb = entry.get("embedding")
            if not cached_emb:
                continue

            sim = _cosine_similarity(q_emb, cached_emb)
            if sim >= SIMILARITY_THRESHOLD:
                logger.info(f"Cache HIT — similarity: {sim:.3f}")
                # Pick 5 random outfits from the pool of 20
                all_outfits = entry.get("outfits", [])
                if len(all_outfits) <= SERVE_SIZE:
                    selected = all_outfits
                else:
                    selected = random.sample(all_outfits, SERVE_SIZE)

                return {"outfits": selected}

        logger.debug("Cache MISS")
        return None

    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def set_cached(params: dict, result: dict) -> None:
    """
    Store a result in Redis with semantic embedding for future lookups.
    """
    redis = _get_redis()
    if redis is None:
        return

    try:
        query = _query_text(params)
        if not query:
            return

        embedding = _embed_query(query)
        key       = _build_cache_key(embedding)
        all_outfits = result.get("outfits", [])

        entry = {
            "embedding": embedding,
            "outfits": all_outfits,  # Store all 20
            "query": query,
        }

        redis.setex(key, CACHE_TTL, json.dumps(entry, ensure_ascii=False))
        logger.info(f"Cache SET — {len(all_outfits)} outfits stored, key: {key}")

    except Exception as e:
        logger.error(f"Cache set error: {e}")