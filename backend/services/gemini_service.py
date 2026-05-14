import io
import json
import logging
from google import genai
from google.genai import types
from config import settings
from services.prompts import (CLOTHING_ANALYSIS_PROMPT, OUTFIT_RECOMMENDATION_PROMPT,
                              OUTFIT_RECOMMENDATION_FALLBACK_PROMPT, CHAT_RECOMMEND_PROMPT)
from utils.image_utils import process_uploaded_image
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable


logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)
GEMINI_MODEL = "gemini-3.1-flash-lite"  # gemini-2.0-flash, gemini-3-flash-preview


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
        logger.error("Gemini request timed out")
        raise RuntimeError("Gemini API request timed out. Please try again.")

    except ServiceUnavailable:
        logger.error("Gemini service unavailable")
        raise RuntimeError("Gemini API is temporarily unavailable. Please try again later.")

    except Exception as e:
        logger.error(f"Unexpected Gemini error: {e}")
        raise RuntimeError(f"Gemini API error: {str(e)}")



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


async def generate_outfit_recommendation(clothing_analysis: dict, concept: str, size: str, color_preference: str, language:str, similar_outfits: list[dict]) -> dict:
    """
    Generate outfit recommendations using RAG.
    Falls back to expertise-only prompt if no similar outfits are found.
    """

    has_context = len(similar_outfits) > 0

    if has_context:
        # Format ChromaDB results as readable context for the prompt
        rag_context = "\n".join([
            f"- {item.get('description', '')}"
            for item in similar_outfits[:10]
        ])
        prompt = OUTFIT_RECOMMENDATION_PROMPT.format(
            color=clothing_analysis.get("color", ""),
            category=clothing_analysis.get("category", ""),
            style=clothing_analysis.get("style", ""),
            pattern=clothing_analysis.get("pattern", ""),
            description=clothing_analysis.get("description", ""),
            size=size,
            concept=concept,
            color_preference=color_preference,
            language=language,
            rag_context=rag_context,
        )
    else:
        # No RAG context — rely on Gemini's fashion knowledge
        prompt = OUTFIT_RECOMMENDATION_FALLBACK_PROMPT.format(
            color=clothing_analysis.get("color", ""),
            category=clothing_analysis.get("category", ""),
            style=clothing_analysis.get("style", ""),
            pattern=clothing_analysis.get("pattern", ""),
            description=clothing_analysis.get("description", ""),
            size=size,
            concept=concept,
            color_preference=color_preference,
            language=language
        )

    raw = _call_gemini(contents=prompt)
    return _parse_json_response(raw)


async def chat_recommend(message: str, concept: str, size: str, color_preference: str, gender: str, weather: str, language: str, additional_notes: str | None, chat_history: list[dict]) -> dict:
    """
    Generate outfit recommendations from text description only.
    No image required — pure chat mode.
    """
    # Format additional notes section
    additional_notes_section = (
        f"- Additional notes: {additional_notes}"
        if additional_notes
        else ""
    )

    # Format chat history for context
    if chat_history:
        history_lines = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in chat_history[-6:]  # Son 6 mesaj — context window'u aşmamak için
        ])
        chat_history_section = f"PREVIOUS CONVERSATION:\n{history_lines}"
    else:
        chat_history_section = ""

    prompt = CHAT_RECOMMEND_PROMPT.format(
        message=message,
        concept=concept,
        size=size,
        color_preference=color_preference,
        gender=gender,
        weather=weather,
        language=language,
        additional_notes_section=additional_notes_section,
        chat_history_section=chat_history_section,
    )

    raw = _call_gemini(contents=prompt)
    result = _parse_json_response(raw)

    # assistant_message ve outfits ayrı döndür
    return {
        "assistant_message": result.get("assistant_message", ""),
        "outfits": result.get("outfits", [])
    }