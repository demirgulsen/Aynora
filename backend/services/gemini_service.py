"""
gemini_service.py — Gemini 3.1 Flash Lite integration with semantic caching.
Handles clothing analysis and outfit recommendation.
Prompts are imported from prompts.py for easy iteration.
"""
import io
import json
import time
import random
import logging
from google import genai
from google.genai import types
from config import settings
from services.prompts import (CLOTHING_ANALYSIS_PROMPT, OUTFIT_RECOMMENDATION_PROMPT,
                              OUTFIT_RECOMMENDATION_FALLBACK_PROMPT, CHAT_RECOMMEND_PROMPT, _SYSTEM_INSTRUCTION)
from utils.image_utils import process_uploaded_image
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable
from services.cache_service import get_cached, set_cached

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)
GEMINI_MODEL = "gemini-3.1-flash-lite"  # gemini-2.0-flash, gemini-3-flash-preview
SERVE_SIZE   = 6   # Number of outfits to return per request


# ── Langfuse client (optional) ────────────────────────────────────────────────
# Fails silently if LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are not set.
def _init_langfuse():
    try:
        import os
        from langfuse import Langfuse
        pk = os.getenv("LANGFUSE_PUBLIC_KEY")
        sk = os.getenv("LANGFUSE_SECRET_KEY")
        if not pk or not sk:
            return None
        return Langfuse(
            public_key=pk,
            secret_key=sk,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
    except Exception:
        return None


_langfuse = _init_langfuse()

# ── Cost constants (Gemini Flash Lite pricing, per token) ─────────────────────
_COST_INPUT_PER_TOKEN = 0.000000075  # $0.075 / 1M input tokens
_COST_OUTPUT_PER_TOKEN = 0.0000003  # $0.30  / 1M output tokens


# ── Helpers ────────────────────────────────────────────────────────────────

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



def _pick_random(outfits: list, n: int = SERVE_SIZE) -> list:
    """Pick n random outfits from pool."""
    if len(outfits) <= n:
        return outfits
    return random.sample(outfits, n)


def compress_rag_context(similar_outfits: list, max_items: int = 10, max_chars: int = 150) -> str:
    """
    Compress ChromaDB RAG results before inserting into prompt.
    Keeps only the most relevant fields and truncates long descriptions,
    staying under ~150 tokens per item to reduce Gemini input cost.
    """
    if not similar_outfits:
        return ""

    lines = []
    for item in similar_outfits[:max_items]:
        meta = item.get("metadata", {}) if isinstance(item, dict) else {}
        category = meta.get("category", "")
        color = meta.get("color", "")
        style = meta.get("style", "")
        desc = str(meta.get("description", ""))[:max_chars]
        lines.append(f"- {category} {color} {style}: {desc}")

    return "\n".join(lines)


# ── Core Gemini call with Langfuse tracing ────────────────────────────────────
def _call_gemini(contents, trace_name: str = "gemini_call", metadata: dict = None) -> str:
    """
    Central Gemini API call with:
      - Error handling (rate limit, timeout, service errors)
      - Langfuse span: latency, token counts, estimated cost
      - system_instruction injected via config (context cache)
    """
    trace = None
    if _langfuse:
        try:
            trace = _langfuse.trace(name=trace_name, metadata=metadata or {})
        except Exception:
            pass

    start = time.perf_counter()

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
            ),
        )
        text = response.text
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Emit Langfuse generation span
        if trace and _langfuse:
            try:
                usage = getattr(response, "usage_metadata", None)
                in_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
                out_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
                cost = (in_tokens * _COST_INPUT_PER_TOKEN) + (out_tokens * _COST_OUTPUT_PER_TOKEN)

                trace.generation(
                    name=trace_name,
                    model=GEMINI_MODEL,
                    input=str(contents)[:500],
                    output=text[:500],
                    usage={"input": in_tokens, "output": out_tokens},
                    metadata={
                        "latency_ms": elapsed_ms,
                        "estimated_cost": round(cost, 6),
                        **(metadata or {}),
                    },
                )
                _langfuse.flush()
            except Exception as lf_err:
                logger.debug(f"Langfuse trace failed (non-critical): {lf_err}")

        return text

    except ResourceExhausted:
        logger.error("Gemini rate limit exceeded")
        raise RuntimeError("Gemini API rate limit exceeded. Please wait and try again.")
    except DeadlineExceeded:
        logger.error("Gemini request timed out.")
        raise RuntimeError("Gemini API request timed out. Please try again.")
    except ServiceUnavailable:
        logger.error("Gemini service unavailable")
        raise RuntimeError("Gemini API is temporarily unavailable. Please try again later.")
    except Exception as e:
        logger.error(f"Unexpected Gemini error: {e}")
        raise RuntimeError(f"Gemini API error: {str(e)}")



# ── Public functions ──────────────────────────────────────────────────

async def analyze_clothing(base64_image: str) -> dict:
    """
    Analyze a clothing item from a base64 image.
    Returns structured metadata: color, category, style, pattern, season, description.
    """
    image, _ = process_uploaded_image(base64_image, save=settings.DEBUG)

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    raw = _call_gemini(
        contents=[
            types.Part.from_bytes(data=img_bytes.read(), mime_type="image/jpeg"),
            types.Part.from_text(text=CLOTHING_ANALYSIS_PROMPT),
        ],
        trace_name="analyze_clothing",
    )

    return _parse_json_response(raw)


async def generate_outfit_recommendation(clothing_analysis: dict, concept: str, size: str, color_preference: str, gender: str, language:str, similar_outfits: list[dict]) -> dict:
    """
    Generate outfit recommendations using RAG.
    Results are semantically cached — similar requests return instantly.
    RAG context is compressed before prompt injection to reduce token cost.
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
    # Compress RAG context — keeps prompt lean (<= 150 tokens per item)
    rag_context = compress_rag_context(similar_outfits) if has_context else ""

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

    raw = _call_gemini(
        contents=prompt,
        trace_name="outfit_recommendation",
        metadata={"concept": concept, "gender": gender, "has_rag": has_context},
    )
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

    # Build chat history section (last 6 messages only — keeps prompt short)
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

    raw = _call_gemini(
        contents=prompt,
        trace_name="chat_recommend",
        metadata={"concept": concept, "gender": gender, "weather": weather},
    )
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