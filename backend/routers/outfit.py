from fastapi import APIRouter, HTTPException
from models.outfit_models import (AnalyzeRequest,  RecommendRequest, AnalyzeResponse, RecommendResponse, ChatRecommendRequest, ChatRecommendResponse,)
from services.gemini_service import analyze_clothing, generate_outfit_recommendation, chat_recommend
from services.clip_service import base64_to_embedding
from services.chroma_service import search_similar_outfits, get_collection_stats
from services.search_service import enrich_outfit_pieces


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
    5. Serper         → Enrich each piece with real images + links
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

        # Enrich with real product images and links
        enriched_outfits = await enrich_outfit_pieces(
            recommendations.get("outfits", [])
        )
        recommendations["outfits"] = enriched_outfits

        return {
            "success": True,
            "analysis": analysis,
            "recommendations": recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/chat-recommend", response_model=ChatRecommendResponse)
async def chat_recommend_endpoint(request: ChatRecommendRequest):
    """
    Text-only pipeline — no image required:
    1. Gemini Text → Generate recommendations from description
    2. Serper      → Enrich each piece with real images + links
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

        # Enrich with real product images and links
        enriched_outfits = await enrich_outfit_pieces(result["outfits"])

        return {
            "success": True,
            "recommendations": {"outfits": enriched_outfits},
            "assistant_message": result["assistant_message"],
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