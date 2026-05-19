"""
dna_router_patch.py
outfit.py router'ına eklenecek Stil DNA endpoint'i.
Kullanıcının beğendiği/beğenmediği kombinlerin embedding ortalamasını
ChromaDB'de "dna_{user_id}" collection'ına kaydeder.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from services.clip_service import text_to_embedding  # varsa; yoksa aşağıya bak
from services.chroma_service import get_or_create_collection
import uuid

router = APIRouter()


class DNAFeedback(BaseModel):
    outfit_title: str
    action: str           # "liked" | "disliked"
    pieces: list[str]     # parça açıklamaları
    user_id: str = "anonymous"


@router.post("/dna-feedback")
async def dna_feedback(feedback: DNAFeedback):
    """
    Stil DNA: beğenilen/beğenilmeyen kombinlerin embedding'ini
    kullanıcıya özel ChromaDB collection'ına ekler.

    Hackathon için basit versiyon:
    - Her liked kombin +1 ağırlık
    - Her disliked kombin -1 ağırlık
    - Sonraki recommend çağrısında bu vektörler RAG'a eklenir
    """
    try:
        # Parça açıklamalarını birleştir → tek embedding
        combined_text = f"{feedback.outfit_title}. " + ". ".join(feedback.pieces)

        # sentence-transformers ile de yapılabilir
        embedding = text_to_embedding(combined_text)

        # Collection: kullanıcı başına
        collection_name = f"dna_{feedback.user_id}"
        collection = get_or_create_collection(collection_name)

        doc_id = str(uuid.uuid4())
        weight = 1.0 if feedback.action == "liked" else -1.0

        collection.add(
            ids=[doc_id],
            documents=[combined_text],
            metadatas=[{
                "outfit_title": feedback.outfit_title,
                "action":       feedback.action,
                "weight":       weight,
            }],
            embeddings=[embedding],
        )

        return {"success": True, "doc_id": doc_id}

    except Exception as e:
        # Hata olsa da frontend'i bloklamıyoruz
        return {"success": False, "error": str(e)}
