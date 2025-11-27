"""
Configuration for integration tests
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio to only use asyncio backend"""
    return "asyncio"
