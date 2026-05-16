"""
outfit.py — Outfit router
Endpoints: /analyze, /recommend, /chat-recommend, /search-piece, /stats
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from models.outfit_models import (
    AnalyzeRequest,
    RecommendRequest,
    AnalyzeResponse,
    RecommendResponse,
    ChatRecommendRequest,
    ChatRecommendResponse,
)
from services.gemini_service import analyze_clothing, generate_outfit_recommendation, chat_recommend
from services.clip_service import base64_to_embedding
from services.chroma_service import search_similar_outfits, get_collection_stats
from services.search_service import enrich_outfit_pieces, search_piece_extended
from services.streaming_service import stream_visual_recommendation, stream_chat_recommendation


router = APIRouter()


@router.post("/recommend/stream")
async def recommend_stream(request: RecommendRequest):
    """
    Streaming visual recommendation pipeline.
    Returns Server-Sent Events — frontend consumes with EventSource.
    """
    return StreamingResponse(
        stream_visual_recommendation(
            base64_image=request.image,
            concept=request.concept,
            size=request.size,
            color_preference=request.color_preference,
            gender=request.gender,
            weather=request.weather,
            language=request.language,
            additional_notes=request.additional_notes,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat-recommend/stream")
async def chat_recommend_stream(request: ChatRecommendRequest):
    """
    Streaming chat recommendation pipeline.
    Returns Server-Sent Events.
    """
    return StreamingResponse(
        stream_chat_recommendation(
            message=request.message,
            concept=request.concept,
            size=request.size,
            color_preference=request.color_preference,
            gender=request.gender,
            weather=request.weather,
            language=request.language,
            additional_notes=request.additional_notes,
            chat_history=[m.model_dump() for m in (request.chat_history or [])],
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )



@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Analyze a clothing item image and return structured metadata."""
    try:
        result = await analyze_clothing(request.image)
        return {"success": True, "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
    Full visual pipeline:
    1. Gemini Vision  → Analyze clothing item
    2. CLIP           → Embedding
    3. ChromaDB       → Similar outfits (RAG)
    4. Gemini Text    → Recommendations
    5. Serper         → Real images + links (parallel)
    """
    try:
        analysis   = await analyze_clothing(request.image)
        embedding  = base64_to_embedding(request.image)

        similar_outfits = search_similar_outfits(
            embedding=embedding,
            n_results=20,
            category_filter=analysis.get("category"),
        )

        recommendations = await generate_outfit_recommendation(
            clothing_analysis=analysis,
            concept=request.concept,
            size=request.size,
            color_preference=request.color_preference,
            gender=request.gender,
            language=request.language,
            similar_outfits=similar_outfits,
        )

        enriched_outfits = await enrich_outfit_pieces(
            recommendations["outfits"],
            gender=request.gender,
        )

        return {
            "success": True,
            "analysis": analysis,
            "recommendations": {"outfits": enriched_outfits},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat-recommend", response_model=ChatRecommendResponse)
async def chat_recommend_endpoint(request: ChatRecommendRequest):
    """
    Text-only pipeline:
    1. Gemini Text → Recommendations
    2. Serper      → Real images + links (parallel)
    """
    try:
        result = await chat_recommend(
            message=request.message,
            concept=request.concept,
            size=request.size,
            color_preference=request.color_preference,
            gender=request.gender,
            weather=request.weather,
            language=request.language,
            additional_notes=request.additional_notes,
            chat_history=[m.model_dump() for m in (request.chat_history or [])],
        )

        enriched_outfits = await enrich_outfit_pieces(
            result["outfits"],
            gender=request.gender,
        )

        return {
            "success": True,
            "recommendations": {"outfits": enriched_outfits},
            "assistant_message": result["assistant_message"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-piece")
async def search_piece(
    query:       str         = Query(..., description="Parça açıklaması"),
    color:       str         = Query("",  description="Renk"),
    gender:      str         = Query("female", description="female | male | unisex"),
    num_results: int         = Query(10,  description="Maksimum sonuç sayısı"),
):
    """
    Extended product search for a single piece.
    Used by the 'Show More' modal in the frontend.
    """
    try:
        results = await search_piece_extended(
            query=query,
            color=color,
            gender=gender,
            num_results=num_results,
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def stats():
    """Return ChromaDB collection stats."""
    try:
        return get_collection_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))