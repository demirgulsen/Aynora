"""
streaming_service.py — Server-Sent Events (SSE) streaming for Gemini responses.
Sends outfit recommendations to frontend as they are generated.

Flow:
1. Send status events as pipeline progresses
2. Stream Gemini response chunks
3. Send final enriched outfits when Serper search completes
"""

import json
import asyncio
import logging
from typing import AsyncGenerator

from services.gemini_service import analyze_clothing, generate_outfit_recommendation, chat_recommend
from services.clip_service import base64_to_embedding
from services.chroma_service import search_similar_outfits
from services.search_service import enrich_outfit_pieces

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event message."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_visual_recommendation(
    base64_image:     str,
    concept:          str,
    size:             str,
    color_preference: str,
    gender:           str,
    weather:          str,
    language:         str,
    additional_notes: str | None,
) -> AsyncGenerator[str, None]:
    """
    Stream visual recommendation pipeline events to frontend.
    Yields SSE strings at each pipeline stage.
    """

    try:
        # Stage 1: Analyzing image
        yield _sse("status", {"stage": "analyzing", "message": "Kıyafet analiz ediliyor..."})
        analysis = await analyze_clothing(base64_image)
        yield _sse("analysis", {"analysis": analysis})

        # Stage 2: Searching similar outfits
        yield _sse("status", {"stage": "searching", "message": "Benzer kombinler aranıyor..."})
        embedding       = base64_to_embedding(base64_image)
        similar_outfits = search_similar_outfits(
            embedding=embedding,
            n_results=20,
            category_filter=analysis.get("category"),
        )

        # Stage 3: Generating recommendations
        yield _sse("status", {"stage": "generating", "message": "Kombin önerileri hazırlanıyor..."})
        recommendations = await generate_outfit_recommendation(
            clothing_analysis=analysis,
            concept=concept,
            size=size,
            color_preference=color_preference,
            gender=gender,
            language=language,
            similar_outfits=similar_outfits,
        )

        # Send raw outfits immediately — frontend shows skeletons filling in
        outfits = recommendations.get("outfits", [])
        yield _sse("outfits_raw", {"outfits": outfits})

        # Stage 4: Enriching with images and links (per outfit, streamed)
        yield _sse("status", {"stage": "enriching", "message": "Ürün görselleri yükleniyor..."})

        enriched = []
        for i, outfit in enumerate(outfits):
            enriched_batch = await enrich_outfit_pieces([outfit], gender=gender)
            enriched.append(enriched_batch[0])

            # Send each enriched outfit as it completes
            yield _sse("outfit_enriched", {
                "index":  i,
                "outfit": enriched_batch[0],
            })

        # Stage 5: Done
        yield _sse("done", {
            "analysis":        analysis,
            "outfits":         enriched,
            "total":           len(enriched),
        })

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield _sse("error", {"message": str(e)})


async def stream_chat_recommendation(
    message:          str,
    concept:          str,
    size:             str,
    color_preference: str,
    gender:           str,
    weather:          str,
    language:         str,
    additional_notes: str | None,
    chat_history:     list[dict],
) -> AsyncGenerator[str, None]:
    """
    Stream chat recommendation pipeline events to frontend.
    """

    try:
        # Stage 1: Generating
        yield _sse("status", {"stage": "generating", "message": "Kombin önerileri hazırlanıyor..."})

        result = await chat_recommend(
            message=message,
            concept=concept,
            size=size,
            color_preference=color_preference,
            gender=gender,
            weather=weather,
            language=language,
            additional_notes=additional_notes,
            chat_history=chat_history,
        )

        outfits           = result.get("outfits", [])
        assistant_message = result.get("assistant_message", "")

        # Send assistant message and raw outfits immediately
        yield _sse("assistant_message", {"message": assistant_message})
        yield _sse("outfits_raw", {"outfits": outfits})

        # Stage 2: Enrich per outfit
        yield _sse("status", {"stage": "enriching", "message": "Ürün görselleri yükleniyor..."})

        enriched = []
        for i, outfit in enumerate(outfits):
            enriched_batch = await enrich_outfit_pieces([outfit], gender=gender)
            enriched.append(enriched_batch[0])
            yield _sse("outfit_enriched", {
                "index":  i,
                "outfit": enriched_batch[0],
            })

        yield _sse("done", {
            "outfits":           enriched,
            "assistant_message": assistant_message,
            "total":             len(enriched),
        })

    except Exception as e:
        logger.error(f"Chat streaming error: {e}")
        yield _sse("error", {"message": str(e)})