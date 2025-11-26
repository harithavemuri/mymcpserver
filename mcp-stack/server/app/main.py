"""MCP Server entry point."""
import os
import sys
import logging
from typing import Any, Dict, Optional, List
from fastapi import FastAPI, HTTPException, Request, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging to stderr as per MCP standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: Log to stderr, not stdout
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="MCP Server",
    version="0.1.0",
    description="MCP Server with data services"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import MCP app after FastAPI app is created to avoid circular imports
from app.mcp_server import create_app, MCPConfig

def configure_app() -> None:
    """Configure the FastAPI application with routes and middleware."""
    # Health check endpoint
    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}
    
    # List MCP prompts endpoint
@app.get("/mcp/prompts")
async def list_mcp_prompts() -> Dict[str, Any]:
    """List all available MCP prompts."""
    try:
        # Use the list_mcp_prompts function from the MCP app
        if hasattr(mcp_app, 'list_mcp_prompts'):
            result = await mcp_app.list_mcp_prompts()
            return result
        # Fallback to direct prompts attribute if available
        elif hasattr(mcp_app, 'prompts'):
            return {"prompts": mcp_app.prompts}
        else:
            return {"error": "No prompts found. Available methods:",
                   "available_methods": [m for m in dir(mcp_app) if not m.startswith('_')]}
    except Exception as e:
        logger.error(f"Error listing MCP prompts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    # List MCP tools endpoint
    @app.get("/mcp/tools")
    async def list_mcp_tools() -> Dict[str, Any]:
        """List all available MCP tools."""
        try:
            if hasattr(mcp_app, 'get_tools'):
                # Await the coroutine if it's a coroutine function
                tools_coro = mcp_app.get_tools()
                if hasattr(tools_coro, '__await__'):
                    tools = await tools_coro
                else:
                    tools = tools_coro
                
                # Handle both sync and async tool lists
                if hasattr(tools, '__aiter__'):
                    tools = [t async for t in tools]
                elif not isinstance(tools, (list, tuple)):
                    tools = list(tools) if hasattr(tools, '__iter__') else [tools]
                    
                return {"tools": [{"name": getattr(t, "__name__", str(t)), 
                                "description": getattr(t, "__doc__", "")} 
                               for t in tools]}
            elif hasattr(mcp_app, 'tools') and isinstance(mcp_app.tools, (list, tuple)):
                return {"tools": [{"name": getattr(t, "__name__", str(t)), 
                                "description": getattr(t, "__doc__", "")} 
                               for t in mcp_app.tools]}
            else:
                return {"error": "No tools found. Available attributes:", 
                       "attributes": [attr for attr in dir(mcp_app) if not attr.startswith('_')]}
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # Add exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

# Import data_loader after FastAPI app is created to avoid circular imports
from app.data.data_loader import data_loader, Customer

# Initialize the app configuration
configure_app()

# Customer details endpoint
@app.get("/api/customers/{customer_id}", response_model=Dict[str, Any])
async def get_customer_endpoint(customer_id: str = Path(..., description="The ID of the customer to retrieve")):
    """
    Get customer details by ID.
    
    Args:
        customer_id: The ID of the customer to retrieve
        
    Returns:
        A dictionary containing the customer's information
    """
    try:
        customer = data_loader.get_customer(customer_id)
        if customer:
            return customer.dict()
        else:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    except Exception as e:
        logger.error(f"Error retrieving customer {customer_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint to verify MCP app mounting
@app.get("/mcp/test")
async def test_mcp():
    return {
        "message": "MCP endpoint is working",
        "mcp_app_type": str(type(mcp_app)) if 'mcp_app' in globals() else "mcp_app not found",
        "has_get_prompts": hasattr(mcp_app, 'get_prompts') if 'mcp_app' in globals() else False,
        "has_prompts_attr": hasattr(mcp_app, 'prompts') if 'mcp_app' in globals() else False
    }

# Create and configure the MCP app
mcp_app = create_app()
logger.info(f"MCP app type: {type(mcp_app)}")

# Mount the MCP app using its http_app method
try:
    # Get the ASGI app from FastMCP
    mcp_asgi_app = mcp_app.http_app()
    # Mount it at /mcp
    app.mount("/mcp", mcp_asgi_app)
    logger.info("Mounted MCP app at /mcp")
except Exception as e:
    logger.error(f"Failed to mount MCP app: {str(e)}", exc_info=True)
    # Fall back to the existing mounting logic if http_app fails
    if hasattr(mcp_app, 'router'):
        app.include_router(mcp_app.router, prefix="/mcp")
        logger.info("Mounted MCP router at /mcp")
    elif hasattr(mcp_app, 'app') and isinstance(mcp_app.app, FastAPI):
        app.mount("/mcp", mcp_app.app)
        logger.info("Mounted MCP FastAPI app at /mcp")
    else:
        logger.warning("No MCP routes mounted. Available attributes on mcp_app:")
        for attr in dir(mcp_app):
            if not attr.startswith('_'):
                attr_type = type(getattr(mcp_app, attr))
                logger.warning(f"- {attr}: {attr_type}")

def run_server(host: str = "0.0.0.0", port: int = 8005, reload: bool = False):
    """Run the server using uvicorn."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()