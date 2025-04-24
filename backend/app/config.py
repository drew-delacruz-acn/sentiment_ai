"""Application configuration settings."""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    # API keys
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # ACN parquet file path
    ACN_PARQUET_PATH: str = os.getenv(
        "ACN_PARQUET_PATH", 
        "/Users/andrewdelacruz/sentiment_ai/backend/app/data/trx_raw_ACN.parquet"
    )
    
    # API settings
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # Cache settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "1800"))  # 30 minutes in seconds
    
    class Config:
        """Pydantic config class."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate essential settings
if not settings.FMP_API_KEY:
    import logging
    logging.warning("FMP_API_KEY not set in environment variables or .env file") 