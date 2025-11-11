"""Configuration settings for the MCP server."""
import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, validator, AnyHttpUrl


class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8005, env="PORT")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    SECRET_KEY: str = Field("your-secret-key-here", env="SECRET_KEY")
    
    # CORS settings
    CORS_ORIGINS: str = Field(
        default="http://localhost:8005,http://127.0.0.1:8005",
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the CORS_ORIGINS string into a list of origins."""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Security
    API_KEY: Optional[str] = Field(None, env="API_KEY")
    
    # Authentication
    AUTH_ENABLED: bool = Field(False, env="AUTH_ENABLED")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Data settings
    DATA_DIR: Path = Field(
        default=Path("data").resolve(),
        description="Directory containing data files"
    )
    
    # Model settings
    MODEL_DIR: Path = Path("models").resolve()
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = ["json", "csv", "parquet"]
    
    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create settings instance
settings = Settings()
