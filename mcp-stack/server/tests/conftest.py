"""Pytest configuration and fixtures for MCP Server tests."""
import os
import asyncio
from typing import Generator, AsyncGenerator

import aiohttp
import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def http_client() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Create and yield an aiohttp ClientSession for making HTTP requests."""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL for the MCP Server."""
    return os.getenv("MCP_SERVER_URL", "http://localhost:8005")


@pytest.fixture(scope="session")
def graphql_endpoint(base_url: str) -> str:
    """Return the GraphQL endpoint URL."""
    return f"{base_url}/graphql"
