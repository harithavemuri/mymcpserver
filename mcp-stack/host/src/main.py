"""Main module for the MCP Host."""
# Set up Python path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import FastAPI, HTTPException, Request, status, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse as FastAPIJSONResponse, JSONResponse
from loguru import logger
from pydantic import BaseModel, Field, HttpUrl

# Security imports
from .security.config_validator import get_settings
from .security.middleware import setup_security_middleware

# Load and validate settings
settings = get_settings()

# Import protocol and models after settings are loaded
from .protocol import MCPHost
from .models import ModelConfig, ModelInfo, PredictionRequest, PredictionResponse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize FastAPI app with default settings
app = FastAPI(
    title="MCP Host",
    description="Model Control Protocol Host for managing and serving ML models",
    version=settings.VERSION if hasattr(settings, 'VERSION') else "0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, 'CORS_ORIGINS', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPClient:
    """Client for interacting with the MCP Server."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize the MCP client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=30.0,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def query_data(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query against the MCP server."""
        payload = {
            "query": query,
            "variables": variables or {},
        }
        if operation_name:
            payload["operationName"] = operation_name
            
        logger.debug(f"Executing GraphQL query: {query[:200]}...")
        
        try:
            response = await self.client.post(
                "/graphql",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result and result["errors"]:
                logger.error(f"GraphQL errors: {result['errors']}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"errors": result["errors"]},
                )
                
            return result.get("data", {})
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"MCP Server error: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Error executing GraphQL query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute query: {str(e)}"
            )
    
    async def query_data_items(
        self,
        source_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Query data items with filtering, sorting, and pagination."""
        query = """
        query GetItems(
            $sourceId: String, 
            $limit: Int, 
            $offset: Int, 
            $filters: JSON,
            $sortBy: String,
            $sortOrder: String
        ) {
            items(
                sourceId: $sourceId,
                limit: $limit,
                offset: $offset,
                filters: $filters,
                sortBy: $sortBy,
                sortOrder: $sortOrder
            ) {
                data
                total
                hasMore
            }
        }
        """
        
        variables = {
            "sourceId": source_id,
            "limit": limit,
            "offset": offset,
            "filters": filters or {},
            "sortBy": sort_by,
            "sortOrder": sort_order.lower()
        }
        
        try:
            result = await self.query_data(query, variables)
            return result.get("items", {"data": [], "total": 0, "hasMore": False})
        except Exception as e:
            logger.error(f"Error querying data items: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query data: {str(e)}"
            )
            
    async def get_data_sources(self) -> List[Dict[str, Any]]:
        """
        Get all available data sources from the MCP Server.
        Since the MCP Server doesn't have a dataSources field, we'll use the available
        query fields to return a list of available data types.
        """
        # Return a list of available data types based on the schema
        return [
            {
                "id": "customers",
                "name": "Customers",
                "description": "Customer data",
                "type": "CUSTOMER"
            },
            {
                "id": "transcripts",
                "name": "Transcripts",
                "description": "Customer interaction transcripts",
                "type": "TRANSCRIPT"
            },
            {
                "id": "tools",
                "name": "Tools",
                "description": "Available tools",
                "type": "TOOL"
            }
        ]
    
    async def query_data_items(
        self,
        source_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Dict[str, Any]:
        """
        Query data items with filtering and pagination.
        
        Args:
            source_id: The type of data to query (e.g., 'customers', 'transcripts', 'tools')
            limit: Maximum number of items to return
            offset: Number of items to skip
            filters: Dictionary of filters to apply
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            Dictionary containing the query results and pagination info
        """
        # Default empty result
        result = {"items": [], "totalCount": 0, "hasNextPage": False}
        
        try:
            if source_id == "customers":
                # Query for customers
                query = """
                query SearchCustomers($filter: CustomerFilterInput!) {
                    searchCustomers(filter: $filter) {
                        customerId
                        firstName
                        lastName
                        email
                        phone
                        # Add other customer fields as needed
                    }
                }
                """
                variables = {
                    "filter": {
                        "limit": limit,
                        "offset": offset,
                        # Add any additional filter criteria here
                    }
                }
                
                response = await self.query_data(query, variables)
                items = response.get("searchCustomers", [])
                
                # Transform to match expected format
                result["items"] = [{
                    "id": item.get("customerId"),
                    "sourceId": "customers",
                    "data": item,
                    "metadata": {},
                    "createdAt": None,
                    "updatedAt": None
                } for item in items]
                
            elif source_id == "transcripts":
                # Query for transcripts
                query = """
                query SearchTranscripts($filter: TranscriptFilterInput!) {
                    searchTranscripts(filter: $filter) {
                        callId
                        customerId
                        callTimestamp
                        callSummary
                        # Add other transcript fields as needed
                    }
                }
                """
                variables = {
                    "filter": {
                        "limit": limit,
                        "offset": offset,
                        # Add any additional filter criteria here
                    }
                }
                
                response = await self.query_data(query, variables)
                items = response.get("searchTranscripts", [])
                
                # Transform to match expected format
                result["items"] = [{
                    "id": item.get("callId"),
                    "sourceId": "transcripts",
                    "data": item,
                    "metadata": {},
                    "createdAt": None,
                    "updatedAt": None
                } for item in items]
                
            elif source_id == "tools":
                # Query for tools
                query = """
                query ListTools($limit: Int, $offset: Int) {
                    listTools(limit: $limit, offset: $offset) {
                        id
                        name
                        description
                        # Add other tool fields as needed
                    }
                }
                """
                # Note: listTools might not require a filter, but check the schema to confirm
                response = await self.query_data(query, {"limit": limit, "offset": offset})
                items = response.get("listTools", [])
                
                # Transform to match expected format
                result["items"] = [{
                    "id": item.get("id"),
                    "sourceId": "tools",
                    "data": item,
                    "metadata": {},
                    "createdAt": None,
                    "updatedAt": None
                } for item in items]
                
            # Update total count based on returned items
            result["totalCount"] = len(result["items"])
            result["hasNextPage"] = len(result["items"]) >= limit
                
        except Exception as e:
            logger.error(f"Error querying data items: {str(e)}")
            
        return result

# Initialize MCP client
mcp_client = MCPClient(
    base_url=settings.MCP_SERVER_URL,
    api_key=settings.API_KEY,
)

# Initialize MCP host
mcp_host = MCPHost(
    server_url=getattr(settings, 'MCP_SERVER_URL', 'http://localhost:8005')
)

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    try:
        # Check if we can connect to the database/microservice
        # For now, we'll just return a simple health check
        return {
            "status": "healthy",
            "version": getattr(settings, "VERSION", "0.1.0"),
            "name": getattr(settings, "HOST_NAME", "mcp-host"),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service unavailable"
        )

# MCP Protocol Endpoints
@app.post("/mcp/register")
async def register_model(model_config: ModelConfig) -> ModelInfo:
    """Register a new model with the host."""
    try:
        return await mcp_host.register_model(model_config)
    except Exception as e:
        logger.error(f"Failed to register model: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@app.post("/mcp/predict")
async def predict(request: PredictionRequest) -> PredictionResponse:
    """Make a prediction using a registered model."""
    try:
        return await mcp_host.predict(request)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

# Data access endpoints
router = APIRouter()

@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_sources():
    """Get all available data sources."""
    return await mcp_client.get_data_sources()

@router.get("/items", response_model=Dict[str, Any])
async def get_items(
    source_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
):
    """Get paginated data items with optional filtering and sorting."""
    return await mcp_client.query_data_items(
        source_id=source_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

class ConversationRequest(BaseModel):
    """Request model for conversation endpoint."""
    query: str = Field(..., description="The natural language query")
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional context to maintain conversation state"
    )

class ConversationResponse(BaseModel):
    """Response model for conversation endpoint."""
    response: str = Field(..., description="Natural language response")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured data from the query"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated conversation context"
    )

@router.post("/converse", response_model=ConversationResponse)
async def converse(request: ConversationRequest):
    """
    Handle natural language conversation and convert to MCP queries.
    
    Example requests:
    - "Show me all customers"
    - "Get details for customer CUST1000"
    - "List recent call transcripts"
    - "Find customer with email example@domain.com"
    - "Is the server healthy?"
    """
    from .conversation import ConversationHandler, QueryIntent
    
    try:
        # Initialize conversation handler with detailed error handling
        logger.info(f"[CONVERSE] Initializing ConversationHandler")
        try:
            handler = ConversationHandler()
            logger.info(f"[CONVERSE] Successfully initialized ConversationHandler")
        except ImportError as ie:
            error_msg = f"[CONVERSE] Import error initializing ConversationHandler: {str(ie)}. Make sure all dependencies are installed."
            logger.error(error_msg, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": error_msg,
                    "error_type": "DependencyError",
                    "suggestion": "Try running: pip install sentence-transformers scikit-learn"
                }
            )
        except Exception as e:
            error_msg = f"[CONVERSE] Error initializing ConversationHandler: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": error_msg,
                    "error_type": "InitializationError",
                    "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
                }
            )
            
        logger.info(f"[CONVERSE] Processing query: {request.query}")
        
        # Parse the natural language query
        try:
            query_params = handler.parse_query(request.query)
            if query_params is None:
                # No intent was matched
                response_text = await handler.format_response(None, {})
                return ConversationResponse(
                    response=response_text,
                    data={"message": "No intent matched"},
                    context=request.context or {}
                )
                
            logger.info(f"[CONVERSE] Successfully parsed query params: {query_params}")
        except Exception as e:
            error_msg = f"[CONVERSE] Error parsing query: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return JSONResponse(
                status_code=400,
                content={
                    "detail": error_msg,
                    "error_type": "QueryParsingError",
                    "query": request.query,
                    "suggestion": "Try rephrasing your query or check for typos."
                }
            )
        
        # Handle health check separately
        if query_params.intent == QueryIntent.HEALTH_CHECK:
            logger.info("[CONVERSE] Handling health check intent")
            try:
                # Try to make a simple request to the server
                health_url = f"{settings.MCP_SERVER_URL}/health"
                logger.info(f"[CONVERSE] Making health check request to: {health_url}")
                
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(health_url, timeout=5.0)
                        response.raise_for_status()
                        health_data = response.json()
                        logger.info(f"[CONVERSE] Health check response: {health_data}")
                        
                        response_text = await handler.format_response(query_params.intent, health_data)
                        logger.info(f"[CONVERSE] Formatted response: {response_text}")
                        
                        return ConversationResponse(
                            response=response_text,
                            data=health_data,
                            context={"last_query": query_params.dict()}
                        )
                
                except httpx.HTTPStatusError as e:
                    error_msg = f"Health check HTTP error: {e.response.status_code} - {e.response.text}"
                    logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
                    return ConversationResponse(
                        response=f"I'm sorry, I couldn't check the server status: {error_msg}",
                        data={"error": error_msg},
                        context={"last_query": query_params.dict()}
                    )
                except httpx.RequestError as e:
                    error_msg = f"Could not connect to MCP server at {settings.MCP_SERVER_URL}: {str(e)}"
                    logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
                    return ConversationResponse(
                        response=f"I'm having trouble connecting to the MCP server. Please make sure it's running at {settings.MCP_SERVER_URL}",
                        data={"error": error_msg},
                        context={"last_query": query_params.dict()}
                    )
                except Exception as e:
                    error_msg = f"Unexpected error during health check: {str(e)}"
                    logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
                    return ConversationResponse(
                        response=f"An unexpected error occurred while checking the server status: {str(e)}",
                        data={"error": error_msg},
                        context={"last_query": query_params.dict()}
                    )
            except Exception as e:
                error_msg = f"Health check failed: {str(e)}"
                logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
                return ConversationResponse(
                    response=f"I'm sorry, I couldn't check the server status: {str(e)}",
                    data={"error": str(e)},
                    context=request.context
                )
        
        # Handle other intents
        logger.info(f"[CONVERSE] Handling intent: {query_params.intent}")
        logger.info(f"[CONVERSE] Query params: {query_params}")
        
        try:
            logger.info(f"[CONVERSE] Querying data items with filters: {query_params.filters}")
            
            # For debugging, let's try a simple query first
            logger.info("[CONVERSE] Testing simple query to MCP server...")
            test_url = f"{settings.MCP_SERVER_URL}/health"
            async with httpx.AsyncClient() as client:
                test_response = await client.get(test_url, timeout=5.0)
                logger.info(f"[CONVERSE] Test query response: {test_response.status_code} - {test_response.text}")
            
            # Now try the actual query
            result = await mcp_client.query_data_items(
                source_id=query_params.filters.get("source_id"),
                limit=query_params.limit,
                offset=query_params.offset,
                filters=query_params.filters,
            )
            logger.info(f"[CONVERSE] Query result: {result}")
            
            # Format the response
            response_text = await handler.format_response(query_params.intent, result)
            logger.info(f"[CONVERSE] Formatted response: {response_text}")
            
            return ConversationResponse(
                response=response_text,
                data=result,
                context={"last_query": query_params.dict()}
            )
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error querying data: {e.response.status_code} - {e.response.text}"
            logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
            return ConversationResponse(
                response=f"I'm sorry, there was an error with your request: {error_msg}",
                data={"error": error_msg},
                context=request.context
            )
        except Exception as e:
            error_msg = f"Error querying data: {str(e)}"
            logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
            return ConversationResponse(
                response=f"I'm sorry, I couldn't process your query: {str(e)}",
                data={"error": str(e)},
                context=request.context
            )
        
    except Exception as e:
        error_msg = f"Error processing conversation: {str(e)}"
        logger.error(f"[CONVERSE] {error_msg}", exc_info=True)
        return ConversationResponse(
            response=f"I'm sorry, I encountered an error processing your request: {str(e)}",
            data={"error": str(e)},
            context=request.context if 'request' in locals() else {}
        )

# Include API routes with /api prefix
app.include_router(router, prefix="/api")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Store settings in app state
        app.state.settings = settings
        
        # Get settings with defaults
        host_name = getattr(settings, 'HOST_NAME', 'unknown')
        
        # Define directories
        model_dir = Path("models")
        data_dir = Path("data")
        
        # Ensure directories exist
        model_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MCP host if available
        if 'mcp_host' in globals():
            await mcp_host.start()  # Added await here
        
        # Test connection to MCP server if client is available
        if 'mcp_client' in globals():
            try:
                sources = await mcp_client.get_data_sources()
                logger.info(f"Connected to MCP Server. Found {len(sources)} data sources.")
            except Exception as e:
                logger.warning(f"Failed to connect to MCP Server: {e}")
                logger.warning("The application will continue to run but may not function correctly without a connection to the MCP Server.")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info(f"Shutting down {settings.HOST_NAME}...")
    await mcp_client.close()
    if hasattr(mcp_host, 'stop'):
        await mcp_host.stop()
    else:
        logger.warning("mcp_host.stop() method not found. Skipping cleanup.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
