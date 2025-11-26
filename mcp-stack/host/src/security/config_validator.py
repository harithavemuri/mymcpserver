"""Configuration validation and security checks."""
import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar, Any

from pydantic import BaseModel, Field, validator, HttpUrl, AnyHttpUrl
from pydantic_settings import BaseSettings
from pydantic.error_wrappers import ValidationError

from ..config import settings

T = TypeVar('T', bound=BaseModel)

def generate_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)

class SecuritySettings(BaseModel):
    """Security-related settings with validation."""
    secret_key: str = Field(default_factory=generate_secret_key)
    jwt_secret: str = Field(default_factory=generate_secret_key)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    cors_origins: List[str] = ["*"]
    rate_limit: int = 60  # requests per minute

    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = True

    @validator("secret_key", "jwt_secret")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

class DatabaseSettings(BaseModel):
    """Database connection settings."""
    url: str = "sqlite:///./mcp_host.db"
    pool_size: int = 20
    echo_sql: bool = False
    ssl_require: bool = False

    class Config:
        env_prefix = "DB_"

class ServerSettings(BaseModel):
    """Server configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8001
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    health_check_interval: int = 30  # seconds

    class Config:
        env_prefix = "SERVER_"

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        valid_environments = ["development", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v.lower()

class ModelSettings(BaseModel):
    """Model configuration settings."""
    model_dir: Path = Path("models").resolve()
    data_dir: Path = Path("data").resolve()
    auto_register_models: bool = True

    class Config:
        env_prefix = "MODEL_"

    @validator("model_dir", "data_dir", pre=True)
    def resolve_paths(cls, v: Any) -> Path:
        if isinstance(v, str):
            path = Path(v).resolve()
        elif isinstance(v, Path):
            path = v.resolve()
        else:
            raise ValueError(f"Expected str or Path, got {type(v)}")

        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return path

class Settings(BaseSettings):
    """Main application settings."""
    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    HOST_NAME: str = Field(default_factory=lambda: f"mcp-host-{os.urandom(4).hex()}", env="HOST_NAME")
    VERSION: str = Field("0.1.0", env="VERSION")

    # MCP Server settings
    MCP_SERVER_URL: str = Field("http://localhost:8005", env="MCP_SERVER_URL")
    API_KEY: Optional[str] = Field(None, env="API_KEY")

    # Security settings
    SECRET_KEY: str = Field(
        default_factory=generate_secret_key,
        env="SECRET_KEY",
        description="Secret key for cryptographic operations"
    )
    JWT_SECRET: str = Field(
        default_factory=generate_secret_key,
        env="JWT_SECRET",
        description="Secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    CORS_ORIGINS: List[str] = Field("*", env="CORS_ORIGINS")
    RATE_LIMIT: int = Field(60, env="RATE_LIMIT")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")

    # Model and data directories
    MODEL_DIR: Path = Field(Path("models").resolve(), env="MODEL_DIR")
    DATA_DIR: Path = Field(Path("data").resolve(), env="DATA_DIR")

    # Feature flags
    AUTO_REGISTER_MODELS: bool = Field(True, env="AUTO_REGISTER_MODELS")

    # Health check
    HEALTH_CHECK_INTERVAL: int = Field(30, env="HEALTH_CHECK_INTERVAL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    def __init__(self, **data):
        # Handle CORS_ORIGINS as a comma-separated string
        if "CORS_ORIGINS" in data and isinstance(data["CORS_ORIGINS"], str):
            data["CORS_ORIGINS"] = [x.strip() for x in data["CORS_ORIGINS"].split(",")]

        # Ensure paths are resolved
        if "MODEL_DIR" in data and isinstance(data["MODEL_DIR"], str):
            data["MODEL_DIR"] = Path(data["MODEL_DIR"]).resolve()
        if "DATA_DIR" in data and isinstance(data["DATA_DIR"], str):
            data["DATA_DIR"] = Path(data["DATA_DIR"]).resolve()

        super().__init__(**data)
        self.validate()

    def validate(self):
        """Validate all settings."""
        if self.ENVIRONMENT == "production":
            self._validate_production_settings()

    def _validate_production_settings(self):
        """Validate production-specific settings."""
        if self.DEBUG:
            raise ValueError("Debug mode should be disabled in production")
        if self.SECRET_KEY == "your-secret-key-here":
            raise ValueError("Change the default secret key in production")
        if self.JWT_SECRET == "your-jwt-secret-here":
            raise ValueError("Change the default JWT secret in production")
        if "*" in self.CORS_ORIGINS and self.ENVIRONMENT == "production":
            raise ValueError("Wildcard CORS is not allowed in production")

def get_settings() -> Settings:
    """Get and validate application settings."""
    settings = Settings()
    settings.validate()
    return settings

def check_environment() -> None:
    """Check if all required environment variables are set."""
    try:
        settings = get_settings()
        print("✅ Environment variables are properly configured")
        return settings
    except ValidationError as e:
        print("❌ Missing or invalid environment variables:")
        for error in e.errors():
            loc = ".".join(str(loc) for loc in error["loc"])
            print(f"  - {loc}: {error['msg']}")
        raise

if __name__ == "__main__":
    # This will validate the environment when run directly
    settings = check_environment()
    print("\nCurrent configuration:")
    print(settings.json(indent=2))
