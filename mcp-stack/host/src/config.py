"""Configuration settings for the MCP Host."""
import os
from pathlib import Path
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Add CORS_ORIGINS at the class level to ensure it's always available
    CORS_ORIGINS: List[str] = ["*"]

    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8001, env="PORT")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    HOST_NAME: str = Field("mcp-host-01", env="HOST_NAME")
    VERSION: str = Field("0.1.0", env="VERSION")
    
    # MCP Server settings
    MCP_SERVER_URL: str = Field(
        default="http://localhost:8005",
        env="MCP_SERVER_URL",
        description="URL of the MCP Server"
    )
    API_KEY: Optional[str] = Field(None, env="API_KEY")
    
    # Model settings
    MODEL_DIR: Path = Field(
        default=Path("models").resolve(),
        description="Directory to store model files"
    )
    
    # Data settings
    DATA_DIR: Path = Field(
        default=Path("data").resolve(),
        description="Directory to store data files"
    )
    
    # CORS settings (comma-separated string of origins, e.g., "http://localhost:3000,http://localhost:8000")
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins",
        alias="CORS_ORIGINS"
    )
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        if v is None:
            return ["*"]
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON array string
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated string
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS_ORIGINS value: {v}")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure CORS_ORIGINS is always set
        if not hasattr(self, 'CORS_ORIGINS') or not self.CORS_ORIGINS:
            self.CORS_ORIGINS = self.cors_origins if hasattr(self, 'cors_origins') else ["*"]
    
    # Model registration settings
    AUTO_REGISTER_MODELS: bool = Field(
        default=True,
        description="Automatically register models on startup"
    )
    
    # Health check settings
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    @validator('MODEL_DIR', 'DATA_DIR', pre=True)
    def resolve_paths(cls, v):
        if isinstance(v, str):
            return Path(v).resolve()
        return v.resolve() if v.exists() else v
    
    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            """Customize settings sources."""
            # Order of priority: env vars > .env file > default values
            return (
                env_settings,
                init_settings,
                file_secret_settings,
            )


# Lazy-loaded settings instance
_settings_instance = None

def get_settings() -> Settings:
    """Get the settings instance, creating it if it doesn't exist."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        # Ensure directories exist
        _settings_instance.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        _settings_instance.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _settings_instance

# For backward compatibility
settings = get_settings()
