from fastapi import APIRouter, HTTPException
from models.outfit_models import (AnalyzeRequest, RecommendRequest, AnalyzeResponse, RecommendResponse)
from services.gemini_service import analyze_clothing, generate_outfit_recommendation
from services.clip_service import base64_to_embedding
from services.chroma_service import search_similar_outfits, get_collection_stats


router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze a clothing item image and return structured metadata.
    Step 1 of the recommendation pipeline.
    """
    try:
        result = await analyze_clothing(request.image)
        return {"success": True, "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
     Full pipeline:
    1. Gemini Vision  → Analyze clothing item
    2. CLIP           → Convert image to embedding
    3. ChromaDB       → Find similar outfits (Visual RAG)
    4. Gemini Text    → Generate personalized recommendations
    """
    try:
        # Step 1: Analyze clothing item with Gemini Vision
        analysis = await analyze_clothing(request.image)

        # Step 2: Generate CLIP embedding for visual similarity search
        embedding = base64_to_embedding(request.image)

        # Step 3: Retrieve visually similar outfits from ChromaDB
        # Filter by detected category to improve relevance
        similar_outfits = search_similar_outfits(
            embedding=embedding,
            n_results=20,
            category_filter=analysis.get("category"),
        )

        # Step 4: Generate recommendations via Gemini RAG
        recommendations = await generate_outfit_recommendation(
            clothing_analysis=analysis,
            concept=request.concept,
            size=request.size,
            color_preference=request.color_preference,
            language=request.language,
            similar_outfits=similar_outfits,
        )

        return {
            "success": True,
            "analysis": analysis,
            "recommendations": recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def stats():
    """
    Return ChromaDB collection stats.
    Useful for verifying the dataset was loaded correctly.
    """
    try:
        return get_collection_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))