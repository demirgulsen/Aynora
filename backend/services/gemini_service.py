"""
gemini_service.py — Gemini 3.1 Flash Lite integration with semantic caching.
Handles clothing analysis and outfit recommendation.
Prompts are imported from prompts.py for easy iteration.
"""
import io
import json
import random
import logging
from google import genai
from google.genai import types
from config import settings
from services.prompts import (CLOTHING_ANALYSIS_PROMPT, OUTFIT_RECOMMENDATION_PROMPT,
                              OUTFIT_RECOMMENDATION_FALLBACK_PROMPT, CHAT_RECOMMEND_PROMPT)
from utils.image_utils import process_uploaded_image
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable
from services.cache_service import get_cached, set_cached

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)
GEMINI_MODEL = "gemini-3.1-flash-lite"  # gemini-2.0-flash, gemini-3-flash-preview
SERVE_SIZE   = 6   # Number of outfits to return per request

def _parse_json_response(raw: str) -> dict:
    """
    Safely parse Gemini's response text as JSON.
    Strips markdown code fences if present.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _call_gemini(contents) -> str:
    """
    Central Gemini API call with error handling.
    Catches rate limit, timeout and service errors with clear messages.
    """
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents
        )
        return response.text

    except ResourceExhausted:
        logger.error("Gemini rate limit exceeded")
        raise RuntimeError("Gemini API rate limit exceeded. Please wait and try again.")
    except DeadlineExceeded:
        logger.error("Gemini request timed out. Please try again.")
        raise RuntimeError("Gemini API request timed out. Please try again.")
    except ServiceUnavailable:
        logger.error("Gemini service unavailable")
        raise RuntimeError("Gemini API is temporarily unavailable. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected Gemini error: {e}")
        raise RuntimeError(f"Gemini API error: {str(e)}")


def _pick_random(outfits: list, n: int = SERVE_SIZE) -> list:
    """Pick n random outfits from pool."""
    if len(outfits) <= n:
        return outfits
    return random.sample(outfits, n)


async def analyze_clothing(base64_image: str) -> dict:
    """
    Analyze a clothing item from a base64 image.
    Returns structured metadata: color, category, style, pattern, season, description.
    """

    # Process and validate the uploaded image
    image, _ = process_uploaded_image(base64_image, save=settings.DEBUG)

    # Convert PIL image to bytes for the new SDK
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    raw = _call_gemini(contents=[
        types.Part.from_bytes(data=img_bytes.read(), mime_type="image/jpeg"),
        types.Part.from_text(text=CLOTHING_ANALYSIS_PROMPT),
    ])

    return _parse_json_response(raw)


async def generate_outfit_recommendation(clothing_analysis: dict, concept: str, size: str, color_preference: str, gender: str, language:str, similar_outfits: list[dict]) -> dict:
    """
    Generate outfit recommendations using RAG.
    Results are semantically cached — similar requests return instantly.
    """
    # Build cache lookup params
    cache_params = {
        "concept": concept,
        "color_preference": color_preference,
        "gender": gender,
        "size": size,
        "language": language,
        "message": clothing_analysis.get("description", ""),
    }

    # Check cache first
    cached = await get_cached(cache_params)
    if cached:
        return cached

    has_context = len(similar_outfits) > 0
    rag_context = "\n".join([
        f"- {item.get('description', '')}" for item in similar_outfits[:10]
    ]) if has_context else ""

    prompt_template = (
        OUTFIT_RECOMMENDATION_PROMPT if has_context
        else OUTFIT_RECOMMENDATION_FALLBACK_PROMPT
    )

    prompt = prompt_template.format(
        color=clothing_analysis.get("color", ""),
        category=clothing_analysis.get("category", ""),
        style=clothing_analysis.get("style", ""),
        pattern=clothing_analysis.get("pattern", ""),
        description=clothing_analysis.get("description", ""),
        size=size,
        concept=concept,
        color_preference=color_preference,
        gender=gender,
        language=language,
        rag_context=rag_context,
    )

    raw = _call_gemini(contents=prompt)
    result = _parse_json_response(raw)
    all_outfits = result.get("outfits", [])

    #  Cache all 20 outfits
    await set_cached(cache_params, {"outfits": all_outfits})
    # Return 6 random
    return {"outfits": _pick_random(all_outfits)}


async def chat_recommend(message: str, concept: str, size: str, color_preference: str, gender: str, weather: str, language: str, additional_notes: str | None, chat_history: list[dict]) -> dict:
    """
    Generate outfit recommendations from text description only.
    Results are semantically cached for high hit rate on similar queries.
    """
    # Cache params — chat_history excluded (conversation-specific)
    cache_params = {
        "message": message,
        "concept": concept,
        "color_preference": color_preference,
        "gender": gender,
        "weather": weather,
        "size": size,
        "language": language,
        "additional_notes": additional_notes or "",
    }

    # Check cache first
    cached = await get_cached(cache_params)
    if cached:
        return {
            "assistant_message": cached.get("assistant_message", ""),
            "outfits": cached.get("outfits", []),
        }

    # Cache MISS — ask Gemini
    chat_history_section = ""
    if chat_history:
        history_lines = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in chat_history[-6:]
        ])
        chat_history_section = f"PREVIOUS CONVERSATION:\n{history_lines}"

    prompt = CHAT_RECOMMEND_PROMPT.format(
        message=message,
        concept=concept,
        size=size,
        color_preference=color_preference,
        gender=gender,
        weather=weather,
        language=language,
        additional_notes_section=f"Notes: {additional_notes}" if additional_notes else "",
        chat_history_section=chat_history_section,
    )

    raw = _call_gemini(contents=prompt)
    result = _parse_json_response(raw)
    all_outfits = result.get("outfits", [])
    assistant_msg = result.get("assistant_message", "")

    # Store in cache
    await set_cached(cache_params, {
        "outfits": all_outfits,
        "assistant_message": assistant_msg,
    })

    # assistant_message ve outfits ayrı döndür
    return {
        "assistant_message": assistant_msg,
        "outfits": _pick_random(all_outfits),
    }