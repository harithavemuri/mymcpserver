"""MCP (Model Context Protocol) implementation for the host."""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

import httpx

from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='MCPMessage')

class MessageType(str, Enum):
    """MCP message types."""
    REGISTER = "register"
    UNREGISTER = "unregister"
    PREDICT = "predict"
    PREDICTION_RESULT = "prediction_result"
    ERROR = "error"

class MCPMessage(BaseModel):
    """Base class for MCP messages."""
    message_type: MessageType
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            Path: str,
        }
    
    @classmethod
    def parse_raw(cls: Type[T], raw: str) -> T:
        """Parse a raw message string into an MCPMessage."""
        try:
            data = json.loads(raw)
            message_type = MessageType(data.get("message_type"))
            message_cls = MESSAGE_TYPES.get(message_type, MCPMessage)
            return message_cls.parse_obj(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse message: {e}")
            raise ValueError(f"Invalid message format: {e}")

class RegisterMessage(MCPMessage):
    """Message sent by a model to register with the host."""
    message_type: MessageType = MessageType.REGISTER
    model_id: str
    model_name: str
    model_version: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)

class PredictMessage(MCPMessage):
    """Message sent to request a prediction."""
    message_type: MessageType = MessageType.PREDICT
    model_id: str
    context_id: str
    input_data: Dict[str, Any]

class PredictionResultMessage(MCPMessage):
    """Message containing prediction results."""
    message_type: MessageType = MessageType.PREDICTION_RESULT
    model_id: str
    request_id: str  # Matches the message_id of the PredictMessage
    output_data: Dict[str, Any]

class ErrorMessage(MCPMessage):
    """Error message."""
    message_type: MessageType = MessageType.ERROR
    error_code: str
    error_message: str
    request_id: Optional[str] = None

# Map message types to their corresponding classes
MESSAGE_TYPES = {
    MessageType.REGISTER: RegisterMessage,
    MessageType.PREDICT: PredictMessage,
    MessageType.PREDICTION_RESULT: PredictionResultMessage,
    MessageType.ERROR: ErrorMessage,
}

class MCPHost:
    """MCP Host implementation."""
    
    def __init__(self, server_url: Optional[str] = None):
        """Initialize the MCP Host."""
        self.server_url = server_url or str(settings.MCP_SERVER_URL)
        self.registered_models: Dict[str, Dict] = {}
        self._http_client = None
    
    async def start(self):
        """Start the MCP host."""
        logger.info("Starting MCP Host...")
        # Initialize HTTP client
        headers = {}
        if hasattr(settings, 'API_KEY') and settings.API_KEY:
            headers["Authorization"] = f"Bearer {settings.API_KEY}"
            
        self._http_client = httpx.AsyncClient(
            base_url=self.server_url,
            headers=headers
        )
        logger.info(f"MCP Host started. Server URL: {self.server_url}")
    
    async def stop(self):
        """Stop the MCP host and clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("MCP Host stopped.")
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming MCP message."""
        try:
            message = MCPMessage.parse_obj(message_data)
            handler = getattr(self, f"_handle_{message.message_type.value}", None)
            
            if not handler:
                return self._create_error_response(
                    "unsupported_message_type",
                    f"Unsupported message type: {message.message_type}",
                    message.message_id
                )
            
            return await handler(message)
            
        except Exception as e:
            logger.exception("Error handling message")
            return self._create_error_response(
                "internal_error",
                str(e),
                message_data.get("message_id") if isinstance(message_data, dict) else None
            )
    
    async def _handle_register(self, message: RegisterMessage) -> Dict[str, Any]:
        """Handle a register message from a model."""
        self.registered_models[message.model_id] = {
            "name": message.model_name,
            "version": message.model_version,
            "capabilities": message.capabilities,
            "last_seen": datetime.now().isoformat(),
        }
        
        logger.info(f"Registered model: {message.model_name} (ID: {message.model_id})")
        return {
            "status": "success",
            "message": f"Model {message.model_name} registered successfully"
        }
    
    async def _handle_predict(self, message: PredictMessage) -> Dict[str, Any]:
        """Handle a predict message."""
        if message.model_id not in self.registered_models:
            return self._create_error_response(
                "model_not_found",
                f"Model {message.model_id} is not registered",
                message.message_id
            )
        
        # In a real implementation, this would dispatch to the appropriate model
        # For now, we'll just return a dummy response
        return {
            "status": "success",
            "request_id": message.message_id,
            "model_id": message.model_id,
            "output": {"result": "dummy_prediction"}
        }
    
    def _create_error_response(
        self,
        error_code: str,
        error_message: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "status": "error",
            "error": {
                "code": error_code,
                "message": error_message,
                "request_id": request_id
            }
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
