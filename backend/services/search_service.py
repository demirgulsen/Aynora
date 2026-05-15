"""
Google Custom Search API integration for Aynora.
Finds real product images and shopping links for outfit pieces.
"""

import httpx
import logging
from config import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Serper Görsel Arama Endpoint'i
SERPER_IMAGES_URL = "https://google.serper.dev/images"

# Shopping-focused query suffix — improves product result quality
SHOPPING_SUFFIX = "satın al mağaza"


async def search_product(query: str, color: str | None = None, num_results: int = 3) -> list[dict]:
    """
    Serper.dev API kullanarak ürün görseli ve linki arar.
    """
    # API Key kontrolü (settings içinde SERPER_API_KEY olduğunu varsayıyorum)
    api_key = getattr(settings, "SERPER_API_KEY", None)

    if not api_key:
        logger.warning("Serper API Key bulunamadı — arama atlanıyor")
        return []

    # Sorguyu oluştur
    search_query = f"{color} {query}" if color else query
    search_query = f"{search_query} {SHOPPING_SUFFIX}"

    # Serper POST gövdesi
    payload = {
        "q": search_query,
        "num": min(num_results, 10),
        "gl": "tr",  # Türkiye sonuçları için
        "hl": "tr",  # Türkçe dil desteği
        "safeSearch": True
    }

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Serper POST isteği kabul eder
            response = await client.post(SERPER_IMAGES_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Serper 'images' anahtarı altında liste döner
        items = data.get("images", [])
        results = []

        for item in items:
            results.append({
                "image_url": item.get("imageUrl", ""),  # Doğrudan resim linki
                "page_url": item.get("link", ""),  # Resmin bulunduğu sayfa (alışveriş linki)
                "title": item.get("title", ""),
                "source": _extract_domain(item.get("link", "")),
            })

        return results

    except httpx.HTTPStatusError as e:
        logger.error(f"Serper API Hatası: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"Arama sırasında beklenmedik hata: {e}")
        return []



async def enrich_outfit_pieces(outfits: list[dict]) -> list[dict]:
    """
    Enrich outfit pieces with real product images and shopping links.
    Called after Gemini generates outfit recommendations.

    For each piece in each outfit:
    → Search Google for matching product
    → Add image_url and page_url to the piece
    """
    enriched_outfits = []

    for outfit in outfits:
        enriched_pieces = []

        for piece in outfit.get("pieces", []):
            # Search for this piece
            results = await search_product(
                query=piece.get("description", ""),
                color=piece.get("color"),
                num_results=2,
            )

            # Add best result to piece
            enriched_piece = {**piece}
            if results:
                enriched_piece["image_url"] = results[0]["image_url"]
                enriched_piece["shopping_links"] = [
                    {
                        "url"   : r["page_url"],
                        "source": r["source"],
                        "title" : r["title"],
                    }
                    for r in results
                    if r["page_url"]
                ]
            else:
                enriched_piece["image_url"] = None
                enriched_piece["shopping_links"] = []

            enriched_pieces.append(enriched_piece)

        enriched_outfits.append({
            **outfit,
            "pieces": enriched_pieces
        })

    return enriched_outfits


def _extract_domain(url: str) -> str:
    """Extract clean domain name from URL for display."""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove www. prefix
        return domain.replace("www.", "")
    except Exception:
        return ""