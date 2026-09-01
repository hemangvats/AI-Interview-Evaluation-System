import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

logger = logging.getLogger(__name__)

DEFAULT_DEV_SECRET = "saathi-super-secret-temp-key-change-in-production-2026"

class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    SECRET_KEY: str = Field(DEFAULT_DEV_SECRET, env="SECRET_KEY")
    MONGODB_URL: str = Field("mongodb://localhost:27017", env="MONGODB_URL")
    MONGODB_DB_NAME: str = Field("ai_interview_bot_db", env="MONGODB_DB_NAME")

auth_settings = AuthSettings()

# Production secret strength validation
if auth_settings.ENVIRONMENT.lower() == "production":
    if not auth_settings.SECRET_KEY or auth_settings.SECRET_KEY == DEFAULT_DEV_SECRET or len(auth_settings.SECRET_KEY) < 32:
        raise RuntimeError("PRODUCTION SECURITY ERROR: SECRET_KEY must be a strong random string (min 32 characters) in production environment.")
elif auth_settings.SECRET_KEY == DEFAULT_DEV_SECRET:
    logger.warning("DEVELOPMENT SECURITY NOTICE: Using default temporary SECRET_KEY. Configure a strong secret in .env for production.")

