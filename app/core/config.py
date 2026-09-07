"""
SatQuery AI - Core Configuration
Pydantic v2 Settings for application configuration.
"""
from typing import List, Union
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SatQuery AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security & Auth
    SECRET_KEY: str = "satquery-super-secret-key-change-in-production-sih26167"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/satquery.db"
    DB_ECHO: bool = False

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: str = "./storage"
    UPLOAD_DIR: str = "./storage/uploads"
    EVIDENCE_DIR: str = "./storage/evidence"
    MODEL_CACHE_DIR: str = "./storage/models"

    # Upload Constraints
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["tif", "tiff", "png", "jpg", "jpeg", "jp2"]

    # Geospatial Processing
    DEFAULT_CRS: str = "EPSG:4326"
    REGISTRATION_METHOD: str = "ecc"
    MAX_IMAGE_DIMENSION: int = 4096
    ENABLE_AUTO_REGISTRATION: bool = True

    # AI Model Settings
    MODEL_DEVICE: str = "cpu"
    MOCK_MODEL_LATENCY: float = 0.3

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()

# Ensure critical storage paths exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.EVIDENCE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.MODEL_CACHE_DIR).mkdir(parents=True, exist_ok=True)
