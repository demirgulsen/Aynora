"""
search_service.py — Serper.dev image search integration
Finds real product images and purchase links for outfit pieces.
All pieces are searched concurrently for maximum speed.
"""

import asyncio
import httpx
import logging
from urllib.parse import urlparse
from config import settings

logger = logging.getLogger(__name__)

SERPER_IMAGES_URL = "https://google.serper.dev/images"
SHOPPING_SUFFIX   = "satın al mağaza"

# Gender query mapping
GENDER_MAP = {
    "female": "kadın",
    "male":   "erkek",
    "unisex": "",
}


async def search_product(
    query:       str,
    color:       str | None = None,
    gender:      str        = "female",
    num_results: int        = 2,
) -> list[dict]:
    """
    Search Serper.dev for product images and shopping links.
    Returns list of {image_url, page_url, title, source}.
    """
    api_key = getattr(settings, "SERPER_API_KEY", None)
    if not api_key:
        logger.warning("SERPER_API_KEY not set — skipping search")
        return []

    gender_tr    = GENDER_MAP.get(gender, "")
    search_query = " ".join(filter(None, [gender_tr, color, query, SHOPPING_SUFFIX]))

    payload = {
        "q":          search_query,
        "num":        min(num_results, 10),
        "gl":         "tr",
        "hl":         "tr",
        "safeSearch": True,
    }

    headers = {
        "X-API-KEY":    api_key,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(SERPER_IMAGES_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        return [
            {
                "image_url": item.get("imageUrl", ""),
                "page_url":  item.get("link", ""),
                "title":     item.get("title", ""),
                "source":    _extract_domain(item.get("link", "")),
            }
            for item in data.get("images", [])[:num_results]
            if item.get("imageUrl") and item.get("link")
        ]

    except httpx.TimeoutException:
        logger.warning(f"Serper timeout: {search_query}")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"Serper HTTP {e.response.status_code}: {search_query}")
        return []
    except Exception as e:
        logger.error(f"Serper error: {e}")
        return []


async def search_piece_extended(
    query:       str,
    color:       str = "",
    gender:      str = "female",
    num_results: int = 10,
) -> list[dict]:
    """
    Extended search for a single piece — used by the
    'Show More' modal in the frontend.
    """
    return await search_product(
        query=query,
        color=color or None,
        gender=gender,
        num_results=num_results,
    )


async def enrich_outfit_pieces(
    outfits: list[dict],
    gender:  str = "female",
) -> list[dict]:
    """
    Enrich all outfit pieces with product images and shopping links.
    All HTTP requests run concurrently — significantly faster than sequential.
    """

    async def enrich_piece(piece: dict) -> dict:
        results = await search_product(
            query=piece.get("description", ""),
            color=piece.get("color"),
            gender=gender,
            num_results=2,
        )
        enriched = {**piece}
        if results:
            enriched["image_url"]      = results[0]["image_url"]
            enriched["shopping_links"] = [
                {
                    "url":    r["page_url"],
                    "source": r["source"],
                    "title":  r["title"],
                }
                for r in results
                if r["page_url"]
            ]
        else:
            enriched["image_url"]      = None
            enriched["shopping_links"] = []
        return enriched

    async def enrich_outfit(outfit: dict) -> dict:
        # All pieces in this outfit searched concurrently
        enriched_pieces = await asyncio.gather(*[
            enrich_piece(piece) for piece in outfit.get("pieces", [])
        ])
        return {**outfit, "pieces": list(enriched_pieces)}

    # All outfits searched concurrently
    enriched_outfits = await asyncio.gather(*[
        enrich_outfit(outfit) for outfit in outfits
    ])
    return list(enriched_outfits)


def _extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    if not url:
        return ""
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""