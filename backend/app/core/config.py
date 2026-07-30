"""Configuration management for the multi-agent WikiLLM system.

This module uses Pydantic Settings to load and validate environment variables
for OpenAI models, Pinecone settings, and other system parameters.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine env file location
_ENV_FILE = ".env"
if os.path.exists("backend/.env"):
    _ENV_FILE = "backend/.env"
elif os.path.exists("../backend/.env"):
    _ENV_FILE = "../backend/.env"

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = "sk-placeholder"
    openai_model_name: str = "gpt-4o-mini"
    openai_embedding_model_name: str = "text-embedding-3-small"

    # Pinecone Configuration
    pinecone_api_key: str = "pcsk_placeholder"
    pinecone_index_name: str = "ikms-rag-agent-system"
    pinecone_environment: str = ""

    # LlamaParse Configuration
    llama_cloud_api_key: str = ""

    # Retrieval Configuration
    retrieval_k: int = 3

    # Turso Edge SQLite Configuration
    turso_database_url: str = ""
    turso_auth_token: str = ""

    # CORS Configuration
    cors_origins: str = "*"

    # Auth Configuration
    google_client_id: str = ""
    jwt_secret_key: str = "wikillm_super_secret_jwt_key_2026_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080  # 7 days

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

# Singleton settings instance
settings: Settings | None = None

def get_settings() -> Settings:
    """Get or create the application settings."""
    global settings
    if settings is None:
        settings = Settings()
    return settings