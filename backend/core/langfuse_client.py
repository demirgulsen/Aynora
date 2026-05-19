"""
langfuse_client.py
Langfuse singleton — her Gemini çağrısında trace + span oluşturur.
Ücretsiz: 50.000 observation/ay (Cloud Hobby tier)
"""

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_langfuse():
    """
    Langfuse istemcisini döndürür.
    .env'de LANGFUSE_PUBLIC_KEY ve LANGFUSE_SECRET_KEY yoksa None döner —
    uygulama Langfuse olmadan çalışmaya devam eder.
    """
    public_key  = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key  = os.getenv("LANGFUSE_SECRET_KEY")
    host        = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
    except ImportError:
        print("[Langfuse] langfuse paketi yüklü değil: pip install langfuse")
        return None
    except Exception as e:
        print(f"[Langfuse] Bağlantı hatası: {e}")
        return None