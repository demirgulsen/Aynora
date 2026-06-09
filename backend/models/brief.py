"""
models/brief.py
═══════════════════════════════════════════════════════════════════════════════
Aynora — Structured Brief Schema
Pipeline'ın ortak veri sözleşmesi. Her servis bu modeli konuşur.

Alt modeller:
  ItemBrief    → Yüklenen / tarif edilen kıyafetin özellikleri
  UserBrief    → Kullanıcı profili (onboardingden)
  ContextBrief → Durum, hava, lokasyon
  SearchBrief  → Arama parametreleri (bütçe, whitelist, long-tail)
  DNABrief     → Kullanıcı stili DNA'sı + cold-start guard

Kritik kural (re-ranker tarafında uygulanır):
  DNABrief.confidence_score < 0.3  →  DNA skoru re-ranking'e dahil EDİLMEZ
  DNABrief.is_cold_start == True   →  Aynı davranış (redundant guard)
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Sabitler — izin verilen değerler (validation + IDE otomatik tamamlama)
# ─────────────────────────────────────────────────────────────────────────────

CategoryType    = Literal["top", "bottom", "dress", "outerwear", "shoes", "accessory", "bag", "other"]
ColorFamilyType = Literal["cool", "warm", "neutral", "earth", "pastel", "neon"]
BudgetTierType  = Literal["budget", "mid", "premium", "luxury"]
LocaleType      = Literal["TR", "EU", "US", "UK", "GLOBAL"]
OccasionType    = Literal[
    "casual", "business_casual", "formal", "smart_casual",
    "sportswear", "evening", "beach", "brunch", "travel", "other"
]
WeatherType = Literal["hot", "mild", "cool", "cold", "rainy", "humid", "sunny"]

DNA_CONFIDENCE_THRESHOLD: float = 0.3  # Bu değerin altında DNA skoru atlanır


# ─────────────────────────────────────────────────────────────────────────────
# 1. ItemBrief — Kıyafet özellikleri
# ─────────────────────────────────────────────────────────────────────────────

class ItemBrief(BaseModel):
    """
    Yüklenen fotoğraf veya metin tarifinden çıkarılan kıyafet özellikleri.
    Gemini Vision veya Query Rewriter tarafından doldurulur.
    """

    category: CategoryType = Field(
        ...,
        description="Kıyafet kategorisi",
        examples=["top", "bottom", "dress"],
    )
    color: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Tam renk adı (İngilizce, lowercase)",
        examples=["navy blue", "off-white", "terracotta"],
    )
    color_family: ColorFamilyType = Field(
        ...,
        description="Renk ailesi — kombin algoritması için kullanılır",
        examples=["cool", "warm", "neutral"],
    )
    fabric: str | None = Field(
        default=None,
        max_length=64,
        description="Kumaş türü (bilinmiyorsa None)",
        examples=["cotton", "linen", "denim", "silk"],
    )
    fit: str | None = Field(
        default=None,
        max_length=64,
        description="Kesim tipi (bilinmiyorsa None)",
        examples=["oversized", "slim", "relaxed", "fitted", "wide-leg"],
    )
    pattern: str | None = Field(
        default=None,
        max_length=64,
        description="Desen tipi (bilinmiyorsa None)",
        examples=["solid", "striped", "floral", "plaid", "geometric"],
    )

    @field_validator("color")
    @classmethod
    def color_lowercase(cls, v: str) -> str:
        return v.strip().lower()


# ─────────────────────────────────────────────────────────────────────────────
# 2. UserBrief — Kullanıcı profili
# ─────────────────────────────────────────────────────────────────────────────

class UserBrief(BaseModel):
    """
    Onboarding akışından veya profil güncellemelerinden gelen kullanıcı verileri.
    Stil Kural Motoru bu verileri avoid_list / prefer_list'i genişletmek için kullanır.
    """

    body_type: str | None = Field(
        default=None,
        max_length=64,
        description="Vücut tipi — onboardingden gelir, None = atlanmış",
        examples=["hourglass", "inverted_triangle", "rectangle", "pear", "apple"],
    )
    size: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Standart beden (EU, US veya TR formatı kabul edilir)",
        examples=["M", "38", "S/M", "XL"],
    )
    avoid_list: list[str] = Field(
        default_factory=list,
        description="Kullanıcının kaçındığı stil, kesim veya detaylar",
        examples=[["boat neck", "wide shoulder emphasis", "crop top"]],
    )
    prefer_list: list[str] = Field(
        default_factory=list,
        description="Kullanıcının tercih ettiği stil veya kesimler",
        examples=[["A-line", "wide leg", "wrap dress"]],
    )

    @field_validator("size")
    @classmethod
    def size_uppercase(cls, v: str) -> str:
        return v.strip().upper()


# ─────────────────────────────────────────────────────────────────────────────
# 3. ContextBrief — Durum & ortam
# ─────────────────────────────────────────────────────────────────────────────

class ContextBrief(BaseModel):
    """
    Kombin önerisinin hedeflediği durum, hava durumu ve coğrafya.
    Stil Kural Motoru bu verilerle whitelist_key üretir.
    """

    occasion: OccasionType = Field(
        ...,
        description="Giyilecek durum / ortam",
        examples=["business_casual", "casual", "evening"],
    )
    weather: WeatherType = Field(
        ...,
        description="Hava durumu — katman önerileri ve kumaş filtresi için",
        examples=["mild", "hot", "cold"],
    )
    formality_score: Annotated[int, Field(ge=1, le=10)] = Field(
        ...,
        description="Resmiyet skoru 1 (tam casual) → 10 (black-tie)",
        examples=[5, 7],
    )
    locale: LocaleType = Field(
        ...,
        description="Kullanıcı lokasyonu — whitelist ve para birimi seçimi",
        examples=["TR", "EU", "US"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. SearchBrief — Arama parametreleri
# ─────────────────────────────────────────────────────────────────────────────

class SearchBrief(BaseModel):
    """
    Serper.dev paralel aramalarının parametreleri.
    Query Rewriter bu modeli kullanarak 3 arama sorgusu üretir.
    """

    budget_tier: BudgetTierType = Field(
        ...,
        description="Bütçe segmenti — sorgu ve marka whitelistini etkiler",
        examples=["budget", "mid", "premium"],
    )
    whitelist_key: str | None = Field(
        default=None,
        max_length=64,
        description=(
            "Dinamik whitelist anahtarı: occasion × budget × locale matrisinden seçilir. "
            "None = global varsayılan whitelist kullanılır."
        ),
        examples=["TR_casual", "global_premium", "EU_business_casual"],
    )
    long_tail_boost: bool = Field(
        default=False,
        description=(
            "True → indie/butik odaklı long-tail sorgular aktif. "
            "Büyük marka sonuçlarının önüne geçer."
        ),
    )
    max_results_per_query: Annotated[int, Field(ge=3, le=20)] = Field(
        default=10,
        description="Her Serper sorgusundan kaç sonuç alınacak (re-ranker öncesi)",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. DNABrief — Kullanıcı stil DNA'sı
# ─────────────────────────────────────────────────────────────────────────────

class DNABrief(BaseModel):
    """
    Feedback loop'tan (click/basket/like/dislike → Redis) beslenen kullanıcı stili.

    Cold-start kuralı:
      is_cold_start == True  VEYA  confidence_score < DNA_CONFIDENCE_THRESHOLD (0.3)
      → Re-ranker DNA skorunu hesaba KATMAZ, tamamen içerik bazlı sıralar.

    Bu sayede yeni kullanıcılar kötü öneri almaz; sistem kör kalmaz.
    """

    is_cold_start: bool = Field(
        ...,
        description=(
            "True → kullanıcıya ait yeterli davranış verisi yok. "
            "Re-ranker DNA ağırlığını sıfırlar."
        ),
    )
    liked_styles: list[str] = Field(
        default_factory=list,
        description="Beğenilen stil etiketleri (feedback'ten türetilir)",
        examples=[["minimalist", "smart_casual", "monochrome"]],
    )
    disliked_colors: list[str] = Field(
        default_factory=list,
        description="Dislike sinyali olan renkler",
        examples=[["neon", "bright_red", "fluorescent_yellow"]],
    )
    past_occasions: list[str] = Field(
        default_factory=list,
        description="Kullanıcının daha önce aradığı durumlar",
        examples=[["office", "brunch", "travel"]],
    )
    confidence_score: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ...,
        description=(
            f"DNA güven skoru [0.0 – 1.0]. "
            f"< {DNA_CONFIDENCE_THRESHOLD} ise re-ranker DNA skorunu atlar."
        ),
        examples=[0.0, 0.45, 0.82],
    )

    @property
    def dna_active(self) -> bool:
        """
        Re-ranker'ın DNA'yı kullanıp kullanmayacağını belirler.
        Tek doğruluk kaynağı — her iki cold-start koşulunu kapsar.

        Kullanım (re-ranker içinde):
            if brief.dna.dna_active:
                score += dna_weight * dna_score
        """
        return (
            not self.is_cold_start
            and self.confidence_score >= DNA_CONFIDENCE_THRESHOLD
        )

    @model_validator(mode="after")
    def sync_cold_start_flag(self) -> "DNABrief":
        """
        confidence_score < threshold ise is_cold_start'ı otomatik True yap.
        İki alan arasındaki tutarsızlığı önler.
        """
        if self.confidence_score < DNA_CONFIDENCE_THRESHOLD and not self.is_cold_start:
            # Sessizce düzelt — uyarı loglanabilir
            object.__setattr__(self, "is_cold_start", True)
        return self


# ─────────────────────────────────────────────────────────────────────────────
# 6. StructuredBrief — Ana sözleşme
# ─────────────────────────────────────────────────────────────────────────────

class StructuredBrief(BaseModel):
    """
    Aynora pipeline'ının tek ortak veri sözleşmesi.

    Veri akışı:
      Gemini Vision / metin → [Stil Kural Motoru] → StructuredBrief
                           → [Query Rewriter]
                           → [Paralel Serper Arama]
                           → [Re-ranker]     ← dna.dna_active burada sorgulanır
                           → [Gemini Final]
                           → SSE stream
    """

    item:    ItemBrief    = Field(..., description="Kıyafet özellikleri")
    user:    UserBrief    = Field(..., description="Kullanıcı profili")
    context: ContextBrief = Field(..., description="Durum ve ortam")
    search:  SearchBrief  = Field(..., description="Arama parametreleri")
    dna:     DNABrief     = Field(..., description="Kullanıcı stil DNA'sı")

    model_config = {
        "json_schema_extra": {
            "example": {
                "item": {
                    "category": "top",
                    "color": "navy blue",
                    "color_family": "cool",
                    "fabric": "cotton",
                    "fit": "relaxed",
                    "pattern": "solid",
                },
                "user": {
                    "body_type": "hourglass",
                    "size": "M",
                    "avoid_list": ["boat neck", "wide shoulder emphasis"],
                    "prefer_list": ["A-line", "wrap style"],
                },
                "context": {
                    "occasion": "business_casual",
                    "weather": "mild",
                    "formality_score": 6,
                    "locale": "TR",
                },
                "search": {
                    "budget_tier": "mid",
                    "whitelist_key": "TR_casual",
                    "long_tail_boost": True,
                    "max_results_per_query": 10,
                },
                "dna": {
                    "is_cold_start": False,
                    "liked_styles": ["minimalist", "smart_casual"],
                    "disliked_colors": ["neon", "bright_red"],
                    "past_occasions": ["office", "brunch"],
                    "confidence_score": 0.72,
                },
            }
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı fabrika — cold-start brief üret (yeni kullanıcı için)
# ─────────────────────────────────────────────────────────────────────────────

def make_cold_dna() -> DNABrief:
    """
    Hiç veri olmayan yeni kullanıcı için güvenli DNABrief üretir.
    Re-ranker otomatik olarak DNA'yı atlar.
    """
    return DNABrief(
        is_cold_start=True,
        liked_styles=[],
        disliked_colors=[],
        past_occasions=[],
        confidence_score=0.0,
    )