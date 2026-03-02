import os
import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("POSTGRES_HOST", "localhost")


@pytest.fixture
def anyio_backend():
    return "asyncio"
