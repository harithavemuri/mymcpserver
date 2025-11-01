"""Pytest configuration and fixtures for the MCP project."""
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fastapi import FastAPI

from mcp.server import MCPServer
from mcp.host import MPCHost
from mcp.config import MCPConfig, TextProcessorConfig, SentimentAnalyzerConfig, KeywordExtractorConfig

# Set up test configuration
TEST_CONFIG = MCPConfig(
    host="0.0.0.0",
    port=8002,
    log_level="debug",
    text_processor=TextProcessorConfig(
        enabled=True,
        to_upper=True,
        to_lower=True,
        title_case=True,
        reverse=False,
        strip=True
    ),
    sentiment_analyzer=SentimentAnalyzerConfig(
        enabled=True,
        analyze_emotion=True,
        analyze_subjectivity=True
    ),
    keyword_extractor=KeywordExtractorConfig(
        enabled=True,
        top_n=5,
        min_word_length=3
    )
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_app() -> FastAPI:
    """Create a test FastAPI application."""
    server = MCPServer(config=TEST_CONFIG)
    return server.app

@pytest.fixture(scope="module")
def async_client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(test_app) as client:
        yield client

@pytest.fixture(scope="module")
async def test_host() -> MPCHost:
    """Create a test MCP host instance."""
    async with MPCHost(base_url="http://localhost:8002") as host:
        yield host
