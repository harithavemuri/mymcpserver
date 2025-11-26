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
from .routers import conversation  # Import the conversation router
from .models import ModelConfig, ModelInfo, PredictionRequest, PredictionResponse
from .text_transform import (
    TextTransformRequest, 
    TextTransformResponse, 
    text_transform_client,
    MCPTextTransformClient
)

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

# Create FastAPI app
app = FastAPI(
    title="MCP Host",
    description="Model Context Protocol Host with Conversation Routing",
    version="0.2.0",
)

# Include routers
app.include_router(conversation.router)

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
    
    async def search_customers(
        self,
        name: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Search for customers with the ability to specify which fields to return.
        
        Args:
            name: Optional name to search for
            fields: List of fields to include in the response
            limit: Maximum number of results to return
            offset: Number of results to skip
            **filters: Additional filter parameters (e.g., email, phone, state)
            
        Returns:
            List of customer dictionaries with only the requested fields
        """
        # Default fields to include if none specified
        if not fields:
            fields = ['id', 'firstName', 'lastName', 'email']
            
        # Always include id field if not already specified
        if 'id' not in fields and 'customerId' not in fields:
            fields.append('id')
            
        # Map field names to match GraphQL schema if needed
        field_mapping = {
            'id': 'customerId',
            'first_name': 'firstName',
            'last_name': 'lastName',
            'phone': 'phone',
            'email': 'email',
            'state': 'state',
            'address': 'address',
            'city': 'city',
            'zip': 'zipCode',
            'country': 'country'
        }
        
        # Map fields to their GraphQL equivalents
        graphql_fields = [field_mapping.get(f, f) for f in fields]
        
        # Construct the GraphQL query
        fields_str = '\n'.join(f'        {f}' for f in graphql_fields)
        
        query = f"""
        query SearchCustomers($filter: CustomerFilterInput!) {{
            searchCustomers(filter: $filter) {{
        {fields_str}
            }}
        }}
        """
        
        # Build filter object with provided parameters
        filter_args = {
            'name': name,
            'limit': limit,
            'offset': offset
        }
        
        # Add additional filters if provided
        valid_filters = ['email', 'phone', 'state', 'city', 'country']
        for key, value in filters.items():
            if key in valid_filters and value is not None:
                filter_args[key] = value
        
        variables = {
            "filter": {k: v for k, v in filter_args.items() if v is not None}
        }
        
        try:
            response = await self.query_data(query, variables)
            customers = response.get("searchCustomers", [])
            
            # Map back to the original field names
            reverse_mapping = {v: k for k, v in field_mapping.items()}
            
            result = []
            for customer in customers:
                mapped_customer = {}
                for gql_field, value in customer.items():
                    field_name = reverse_mapping.get(gql_field, gql_field)
                    mapped_customer[field_name] = value
                result.append(mapped_customer)
                
            return result
            
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return []
    
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

# Text Transform Endpoints

@app.post("/api/text/transform", response_model=TextTransformResponse)
async def transform_text(request: TextTransformRequest):
    """Transform text using the specified operation."""
    try:
        return await text_transform_client.transform(
            text=request.text,
            operation=request.operation,
            options=request.options or {}
        )
    except Exception as e:
        logger.error(f"Text transformation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Text transformation failed: {str(e)}"
        )

@app.get("/api/text/operations", response_model=list[str])
async def get_text_operations():
    """Get available text transformation operations."""
    try:
        return await text_transform_client.get_available_operations()
    except Exception as e:
        logger.error(f"Failed to get text operations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get text operations: {str(e)}"
        )

# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
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

# ... (rest of the code remains the same)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        logger.info("Shutting down MCP host...")
        if 'mcp_host' in globals():
            await mcp_host.close()
        if 'mcp_client' in globals():
            await mcp_client.close()
        if 'text_transform_client' in globals():
            await text_transform_client.close()
        logger.info("MCP host shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
