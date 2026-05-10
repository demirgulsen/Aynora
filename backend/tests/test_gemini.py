"""
Quick Gemini connection test — run once to verify setup.
Usage: python test_gemini.py

This file is NOT part of the app, delete after testing.
"""

import asyncio
import sys
import os
import pytest
from services.gemini_service import _call_gemini, _parse_json_response
from config import settings
# Allow imports from backend root
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()


@pytest.mark.asyncio
async def test_connection():
    print(f"Model  : {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug  : {settings.DEBUG}")
    print(f"API Key: {'SET ✅' if settings.GEMINI_API_KEY != 'your_gemini_api_key_here' else 'NOT SET ❌'}\n")

    # --- Test 1: Basic connection ---
    print("Test 1 — Basic connection...")
    try:
        raw = _call_gemini("Say exactly: CONNECTION_OK")
        print(f"  Response : {raw.strip()}")
        print("  Result   : ✅ PASSED\n")
    except Exception as e:
        print(f"  Result   : ❌ FAILED — {e}\n")
        return

    # --- Test 2: JSON parsing ---
    print("Test 2 — JSON response parsing...")
    try:
        raw = _call_gemini(
            'Return this exact JSON, no extra text: {"status": "ok", "model": "gemini"}'
        )
        parsed = _parse_json_response(raw)
        assert parsed.get("status") == "ok", "Unexpected JSON content"
        print(f"  Parsed   : {parsed}")
        print("  Result   : ✅ PASSED\n")
    except Exception as e:
        print(f"  Result   : ❌ FAILED — {e}\n")

    # --- Test 3: Fashion prompt (no image) ---
    print("Test 3 — Fashion prompt...")
    try:
        raw = _call_gemini(
            "Name 2 colors that go well with navy blue. "
            "Return JSON: {\"colors\": [\"color1\", \"color2\"]}"
        )
        parsed = _parse_json_response(raw)
        assert "colors" in parsed, "Missing 'colors' key"
        print(f"  Colors   : {parsed['colors']}")
        print("  Result   : ✅ PASSED\n")
    except Exception as e:
        print(f"  Result   : ❌ FAILED — {e}\n")

    print("All tests complete.")


if __name__ == "__main__":
    asyncio.run(test_connection())