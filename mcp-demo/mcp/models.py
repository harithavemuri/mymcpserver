from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from typing import Literal

class ToolName(str, Enum):
    """Enumeration of available tools in the MCP system."""
    TEXT_PROCESSOR = "text_processor"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    KEYWORD_EXTRACTOR = "keyword_extractor"


class TextRequest(BaseModel):
    """Request model for text processing."""
    text: str = Field(..., description="The text to be processed")
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional parameters for processing"
    )


class ToolResponse(BaseModel):
    """Response model for individual tool execution."""
    tool_name: ToolName
    result: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingResult(BaseModel):
    """Result of processing text through the MCP workflow."""
    original_text: str = Field(..., description="The original input text")
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from each tool in the workflow, keyed by tool name"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the processing"
    )

    # Pydantic v2 model configuration
    model_config = {
        # Allow extra fields to be included in the model
        "extra": "allow",
        # Allow population by field name (e.g., 'text_processor' and 'sentiment_analyzer')
        "populate_by_name": True
    }


class BatchTextRequest(BaseModel):
    """Request model for processing multiple texts."""
    texts: List[str] = Field(..., description="List of texts to process")
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional parameters for processing"
    )
    max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of concurrent processing tasks"
    )


class BatchTextResponse(BaseModel):
    """Response model for batch text processing."""
    success: bool
    results: List[Dict[str, Any]]
    processed_count: int
    error: Optional[str] = None


class TextResponse(BaseModel):
    """Final response model for the MCP API."""
    success: bool
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None


class ToolConfig(BaseModel):
    """Base configuration for MCP tools."""
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
    """Configuration for the MCP server."""
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
    log_level: str = Field(
        default="info",
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
    model_config = {
        "use_enum_values": True,
        "extra": "forbid",
        "validate_assignment": True
    }


class WorkflowState(BaseModel):
    """State object for the LangGraph workflow."""
    input_text: str = Field(..., description="The input text to be processed")
    results: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Results from each tool in the workflow, keyed by tool name"
    )
    current_tool: Optional[str] = Field(
        default=None,
        description="Name of the current tool being executed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if any tool fails"
    )

    # Pydantic v2 model configuration
    model_config = {
        # Allow extra fields to be included in the model
        "extra": "allow",
        # Allow population by field name
        "populate_by_name": True
    }
