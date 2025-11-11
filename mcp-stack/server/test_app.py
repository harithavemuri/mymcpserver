"""Test FastAPI application to verify basic functionality."""
from fastapi import FastAPI

app = FastAPI(
    title="Test MCP Server",
    description="Test application for MCP Server",
    version="0.1.0"
)

@app.get("/")
async def read_root():
    """Root endpoint that returns a simple message."""
    return {"message": "Test MCP Server is running!"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_app:app", host="0.0.0.0", port=8005, reload=True)
