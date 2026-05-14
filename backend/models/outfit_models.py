from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ------------------------------------------------------------
# ENUMS — Constrained value sets for user inputs
# ------------------------------------------------------------

class Language(str, Enum):
    turkish = "tr"
    english = "en"


class Concept(str, Enum):
    wedding = "wedding"
    business = "business"
    casual = "casual"
    special_invitation = "special_invitation"
    sport = "sport"
    date = "date"
    night_out ="night_out"
    graduation="graduation"
    home_loungewear="home_loungewear"
    interview="interview"


class Size(str, Enum):
    xs = "XS"
    s = "S"
    m = "M"
    l = "L"
    xl = "XL"
    xxl = "XXL"


class ColorPreference(str, Enum):
    neutral = "neutral"
    vibrant = "vibrant"
    pastel = "pastel"
    dark = "dark"
    light = "light"
    monochrome = "monochrome"
    earth_tones = "earth_tones"
    metallic = "metallic"
    no_preference = "no_preference"


class Gender(str, Enum):
    unisex = "unisex"
    male = "male"
    female = "female"


class Weather(str, Enum):
    sunny = "sunny"
    rainy = "rainy"
    cold = "cold"
    hot = "hot"


class ChatMessage(BaseModel):
    role: str        # "user" or "assistant"
    content: str

# ------------------------------------------------------------
# REQUEST MODELS
# ------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image string")
    concept: Concept = Field(..., description="Occasion or dress code")
    size: Size = Field(..., description="User's clothing size")
    color_preference: ColorPreference = Field(
        default=ColorPreference.no_preference,
        description="User's color preference for outfit suggestions"
    )


class RecommendRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image string")
    concept: Concept = Field(..., description="Occasion or dress code")
    size: Size = Field(..., description="User's clothing size")
    color_preference: ColorPreference = Field(
        default=ColorPreference.no_preference,
        description="User's color preference"
    )
    gender: Gender = Field(default=Gender.unisex)
    weather: Weather = Field(default=Weather.sunny)
    additional_notes: Optional[str] = Field(None, description="For example: Vintage, just linen pieces, etc.")
    language: Language = Field(default=Language.turkish)


class ChatRecommendRequest(BaseModel):
    message: str = Field(..., description="User's combination request")
    concept: Concept = Field(default=Concept.casual)
    size: Size = Field(default=Size.m)
    color_preference: ColorPreference = Field(default=ColorPreference.no_preference)
    gender: Gender = Field(default=Gender.unisex)
    weather: Weather = Field(default=Weather.sunny)
    language: Language = Field(default=Language.turkish)
    additional_notes: Optional[str] = None
    chat_history: Optional[list[ChatMessage]] = Field(
        default=[],
        description="Previous messages — for multi-turn conversation"
    )

# ------------------------------------------------------------
# RESPONSE MODELS
# ------------------------------------------------------------

class ClothingAnalysis(BaseModel):
    color: str
    category: str
    style: str
    pattern: str
    season: str
    description: str
    material: Optional[str] = None
    fit: Optional[str] = None


class OutfitPiece(BaseModel):
    category: str
    description: str
    color: str
    where_to_find: str
    image_url: Optional[str] = None
    confidence_score: Optional[float] = None


class OutfitItem(BaseModel):
    title: str
    description: str
    pieces: list[OutfitPiece]
    overall_comment: str


class RecommendationResult(BaseModel):
    outfits: list[OutfitItem]


class AnalyzeResponse(BaseModel):
    success: bool
    analysis: ClothingAnalysis


class RecommendResponse(BaseModel):
    success: bool
    analysis: ClothingAnalysis
    recommendations: RecommendationResult


class ChatRecommendResponse(BaseModel):
    success: bool
    recommendations: RecommendationResult
    assistant_message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None