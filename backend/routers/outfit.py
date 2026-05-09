from fastapi import APIRouter, HTTPException
from models.outfit_models import (AnalyzeRequest, RecommendRequest, AnalyzeResponse, RecommendResponse)
from services.gemini_service import analyze_clothing, generate_outfit_recommendation


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
    """ Full pipeline: analyze → search similar outfits → generate recommendations. """
    try:
        # Step 1: Analyze the uploaded clothing item
        analysis = await analyze_clothing(request.image)

        # Step 2: Placeholder — ChromaDB search will be added
        similar_outfits = []

        # Step 3: Generate recommendations (fallback mode until RAG is ready)
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