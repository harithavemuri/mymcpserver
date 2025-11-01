"""
MCP (Model Context Protocol) - A protocol for model communication and workflow orchestration.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic
from enum import Enum

# Import MCPConfig from models to ensure we're using the complete version
from .models import MCPConfig

class ToolName(str, Enum):
    """Enumeration of available tools in the MCP system."""
    TEXT_PROCESSOR = "text_processor"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    KEYWORD_EXTRACTOR = "keyword_extractor"

class TextRequest(BaseModel):
    """Request model for text processing."""
    text: str
    params: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    """Response model for tool execution."""
    tool_name: str
    result: Dict[str, Any]
    metadata: Dict[str, Any] = {}

class WorkflowState(BaseModel):
    """State model for the workflow."""
    input_text: str
    results: Dict[str, Any] = {}
    current_tool: Optional[str] = None
    error: Optional[str] = None

# MCPConfig is now imported from models.py

# Import server and host after models to avoid circular imports
from .server import MCPServer
from .host import MPCHost
from .workflow import create_workflow, Workflow

__version__ = "0.2.0"
__all__ = [
    "MCPServer",
    "MPCHost",
    "MCPConfig",
    "ToolName",
    "TextRequest",
    "ToolResponse",
    "WorkflowState",
    "create_workflow",
    "Workflow"
]
