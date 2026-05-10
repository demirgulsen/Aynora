# ============================================================
# Centralized application settings
# Reads all configuration from environment variables / .env file.
# ============================================================
import os
from typing import ClassVar, Set, Tuple
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Gemini API
    GEMINI_API_KEY: str

    # ChromaDB persistent storage path
    CHROMA_DB_PATH: str = "../data/chroma_db"

    # CORS — comma-separated list of allowed origins
    # Example in .env: CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # App metadata
    APP_NAME: str = "Aynora"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Upload settings
    MAX_IMAGE_SIZE_MB: int = 5
    UPLOAD_DIR: str = "static/uploads"

    # Supported input formats
    ALLOWED_FORMATS: ClassVar[Set[str]] = {"JPEG", "PNG", "WEBP"}

    # Max dimensions before resizing (CLIP works best with 224x224,
    # but we keep a larger size for Gemini Vision quality)
    MAX_SIZE: ClassVar[Tuple[int, int]] = (1024, 1024)



# Single instance — import this everywhere
settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)