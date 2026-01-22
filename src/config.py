"""
Centralized configuration management using Pydantic Settings.
All environment variables are loaded and validated here.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Chatbot TamLy"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_change_in_production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # JWT Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "chatbot_db")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct async PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # AI Services
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Chroma (Internal Docker Network)
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chroma")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    
    # CORS - Support both string and list from environment
    BACKEND_CORS_ORIGINS: list = [
        origin.strip() 
        for origin in os.getenv(
            "BACKEND_CORS_ORIGINS", 
            "http://localhost,http://localhost:80,http://localhost:8080"
        ).split(",")
    ]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "True").lower() == "true"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
    
    def validate_production_config(self):
        """
        Validate configuration for production deployment.
        Raises ValueError if critical settings are insecure.
        """
        if not self.DEBUG:  # Production mode
            # Validate SECRET_KEY
            if self.SECRET_KEY == "dev_secret_change_in_production":
                raise ValueError(
                    "SECURITY ERROR: SECRET_KEY must be changed in production! "
                    "Generate a secure key with: openssl rand -hex 32"
                )
            
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECURITY ERROR: SECRET_KEY must be at least 32 characters long!"
                )
            
            # Validate CORS origins
            if "*" in str(self.BACKEND_CORS_ORIGINS):
                raise ValueError(
                    "SECURITY ERROR: BACKEND_CORS_ORIGINS cannot be '*' in production! "
                    "Specify exact domains."
                )


settings = Settings()

# Auto-validate in production mode
if not settings.DEBUG:
    settings.validate_production_config()
