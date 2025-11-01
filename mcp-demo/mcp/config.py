"""Configuration settings for the MCP server."""
from typing import Optional, Dict, Any, List, Literal
from enum import Enum, auto
from pydantic import BaseModel, Field, validator, ConfigDict

class LogLevel(str, Enum):
    """Available log levels for the application."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ToolConfig(BaseModel):
    """Base configuration for tools."""
    enabled: bool = Field(default=True, description="Whether the tool is enabled")

class TextProcessorConfig(ToolConfig):
    """Configuration for the text processor tool."""
    to_upper: bool = Field(default=True, description="Convert text to uppercase")
    to_lower: bool = Field(default=True, description="Convert text to lowercase")
    title_case: bool = Field(default=True, description="Convert text to title case")
    reverse: bool = Field(default=False, description="Reverse the text")
    strip: bool = Field(default=True, description="Strip whitespace from the text")

class SentimentAnalyzerConfig(ToolConfig):
    """Configuration for the sentiment analyzer tool."""
    analyze_emotion: bool = Field(default=True, description="Perform emotion analysis")
    analyze_subjectivity: bool = Field(default=True, description="Perform subjectivity analysis")

class KeywordExtractorConfig(ToolConfig):
    """Configuration for the keyword extractor tool."""
    top_n: int = Field(default=5, ge=1, description="Number of top keywords to extract")
    min_word_length: int = Field(default=3, ge=1, description="Minimum word length for keywords")

class MCPConfig(BaseModel):
    """Configuration model for the MCP server."""
    host: str = Field(
        default="0.0.0.0",
        description="Host address to bind the server to."
    )
    port: int = Field(
        default=8001,
        ge=1024,
        le=65535,
        description="Port to run the server on (1024-65535)."
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level for the application."
    )
    debug: bool = Field(
        default=False,
        description="Run the server in debug mode."
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development."
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="List of allowed origins for CORS."
    )
    
    # Tool configurations
    text_processor: TextProcessorConfig = Field(
        default_factory=TextProcessorConfig,
        description="Configuration for the text processor tool"
    )
    sentiment_analyzer: SentimentAnalyzerConfig = Field(
        default_factory=SentimentAnalyzerConfig,
        description="Configuration for the sentiment analyzer tool"
    )
    keyword_extractor: KeywordExtractorConfig = Field(
        default_factory=KeywordExtractorConfig,
        description="Configuration for the keyword extractor tool"
    )
    
    # Pydantic v2 config
    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        validate_assignment=True
    )

# Default configuration
DEFAULT_CONFIG = MCPConfig()
