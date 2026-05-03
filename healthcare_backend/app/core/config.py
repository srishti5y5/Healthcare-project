"""
app/core/config.py
Centralised settings — loaded once at startup from .env
"""
from functools import lru_cache
from typing import List

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/healthcare_db"

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE-ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── ML ────────────────────────────────────────────────────────────────────
    MODEL_PATH: str = "app/ml/model.joblib"
    TRAINING_DATA_PATH: str = "data/india_healthcare_district_data.csv"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()          # instantiated once; safe to import anywhere
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
