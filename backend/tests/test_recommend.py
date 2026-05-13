"""
/outfit/recommend endpoint integration tests.
Real Gemini API calls with rate limit handling.

Usage:
    cd backend
    pytest tests/test_recommend_endpoint.py -v -s

Requirements:
    - Server running: uvicorn main:app --reload --port 8003
    - GEMINI_API_KEY set in .env
    - Run from backend/ directory
"""

import pytest
import requests
import base64
import io
import time
from PIL import Image

BASE_URL = "http://127.0.0.1:8003"

# Gemini free tier: 20 req/day, ~2 req/min
# Her test çifti (analyze + recommend) = 2 istek
# Testler arası 35 saniye bekleme rate limit'i aşmaz
RATE_LIMIT_DELAY = 60


# ── Fixtures

@pytest.fixture(scope="module")
def black_top_b64() -> str:
    """Solid black image — stand-in for a black top."""
    img = Image.new("RGB", (224, 224), color=(10, 10, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.fixture(scope="module")
def white_shirt_b64() -> str:
    """Solid white image — stand-in for a white shirt."""
    img = Image.new("RGB", (224, 224), color=(245, 245, 245))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.fixture(autouse=True)
def rate_limit_wait(request):
    """Wait between tests to avoid Gemini rate limits."""
    yield
    # Skip wait for non-Gemini tests
    if request.node.cls and request.node.cls.__name__ == "TestServerHealth":
        return
    print(f"\n  ⏳ Rate limit wait {RATE_LIMIT_DELAY}s...")
    time.sleep(RATE_LIMIT_DELAY)


def post_recommend(b64: str, **kwargs) -> tuple[int, dict]:
    payload = {
        "image": b64,
        "concept": "casual",
        "size": "M",
        "color_preference": "neutral",
        "gender": "female",
        "language": "tr",
        "weather": "sunny",
        **kwargs,
    }
    r = requests.post(f"{BASE_URL}/outfit/recommend", json=payload, timeout=60)
    return r.status_code, r.json()


def assert_valid_response(data: dict, label: str = ""):
    """Common assertions for a valid recommendation response."""
    assert data.get("success") is True, f"[{label}] success=False, got: {data}"
    assert "analysis" in data, f"[{label}] Missing analysis"
    assert "recommendations" in data, f"[{label}] Missing recommendations"

    analysis = data["analysis"]
    for field in ["color", "category", "style", "pattern", "season", "description"]:
        assert analysis.get(field), f"[{label}] Analysis missing: {field}"

    outfits = data["recommendations"]["outfits"]
    assert len(outfits) >= 3, f"[{label}] Expected at least 3 outfits, got {len(outfits)}"

    for i, outfit in enumerate(outfits):
        for field in ["title", "description", "pieces", "overall_comment"]:
            assert outfit.get(field), f"[{label}] Outfit {i+1} missing: {field}"
        assert len(outfit["pieces"]) >= 2, f"[{label}] Outfit {i+1} has too few pieces"
        for piece in outfit["pieces"]:
            for field in ["category", "description", "color", "where_to_find"]:
                assert piece.get(field), f"[{label}] Piece missing: {field}"


# ── Server Health

class TestServerHealth:

    def test_health_endpoint(self):
        """Server must be reachable."""
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_chromadb_has_data(self):
        """ChromaDB must have outfit data."""
        r = requests.get(f"{BASE_URL}/outfit/stats", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["total_items"] > 0, "ChromaDB is empty!"
        print(f"\n  ChromaDB items: {data['total_items']:,}")

    def test_missing_image_returns_422(self):
        """Request without image must return 422."""
        r = requests.post(
            f"{BASE_URL}/outfit/recommend",
            json={"concept": "casual", "size": "M", "color_preference": "neutral"},
            timeout=10
        )
        assert r.status_code == 422

    def test_invalid_concept_returns_422(self, black_top_b64):
        """Invalid concept enum must return 422."""
        r = requests.post(
            f"{BASE_URL}/outfit/recommend",
            json={"image": black_top_b64, "concept": "invalid", "size": "M", "color_preference": "neutral"},
            timeout=10
        )
        assert r.status_code == 422

    def test_invalid_size_returns_422(self, black_top_b64):
        """Invalid size enum must return 422."""
        r = requests.post(
            f"{BASE_URL}/outfit/recommend",
            json={"image": black_top_b64, "concept": "casual", "size": "XXXL", "color_preference": "neutral"},
            timeout=10
        )
        assert r.status_code == 422


# ── Scenario Tests

class TestScenarios:

    def test_scenario_1_casual_female_neutral(self, black_top_b64):
        """Scenario 1 — Casual, female, neutral."""
        status, data = post_recommend(black_top_b64, concept="casual", gender="female", color_preference="neutral")
        assert status == 200, f"Got {status}: {data}"
        assert_valid_response(data, "casual_female_neutral")
        print(f"\n  Titles: {[o['title'] for o in data['recommendations']['outfits']]}")

    def test_scenario_2_wedding_female_pastel(self, white_shirt_b64):
        """Scenario 2 — Wedding, female, pastel."""
        status, data = post_recommend(white_shirt_b64, concept="wedding", gender="female", color_preference="pastel")
        assert status == 200, f"Got {status}: {data}"
        assert_valid_response(data, "wedding_female_pastel")
        print(f"\n  Titles: {[o['title'] for o in data['recommendations']['outfits']]}")

    def test_scenario_3_business_male_english(self, white_shirt_b64):
        """Scenario 3 — Business, male, English response."""
        status, data = post_recommend(white_shirt_b64, concept="business", gender="male", language="en")
        assert status == 200, f"Got {status}: {data}"
        assert_valid_response(data, "business_male_english")
        all_text = " ".join([o["title"] for o in data["recommendations"]["outfits"]]).lower()
        english_words = ["the", "and", "style", "look", "classic", "modern", "smart", "chic"]
        assert any(w in all_text for w in english_words), f"Not English: {all_text}"
        print(f"\n  Titles: {[o['title'] for o in data['recommendations']['outfits']]}")

    def test_scenario_4_sport_vibrant(self, black_top_b64):
        """Scenario 4 — Sport, vibrant colors."""
        status, data = post_recommend(black_top_b64, concept="sport", color_preference="vibrant")
        assert status == 200, f"Got {status}: {data}"
        assert_valid_response(data, "sport_vibrant")
        print(f"\n  Titles: {[o['title'] for o in data['recommendations']['outfits']]}")

    def test_scenario_5_special_invitation_dark(self, black_top_b64):
        """Scenario 5 — Special invitation, dark colors."""
        status, data = post_recommend(black_top_b64, concept="special_invitation", color_preference="dark")
        assert status == 200, f"Got {status}: {data}"
        assert_valid_response(data, "special_invitation_dark")
        print(f"\n  Titles: {[o['title'] for o in data['recommendations']['outfits']]}")

    def test_scenario_6_turkish_language(self, black_top_b64):
        """Language test — Turkish response must contain Turkish text."""
        status, data = post_recommend(black_top_b64, language="tr")
        assert status == 200
        all_text = " ".join([
            o["title"] + " " + o["description"]
            for o in data["recommendations"]["outfits"]
        ]).lower()
        turkish_words = ["ve", "ile", "için", "bir", "bu", "şık", "renk", "kombin", "giyim"]
        assert any(w in all_text for w in turkish_words), f"Not Turkish: {all_text[:200]}"
        print(f"\n  Sample TR: {all_text[:100]}")