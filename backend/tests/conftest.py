import asyncio
import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Insert backend directory into python path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

TEST_DB_PATH = Path("./test_patchpilot.db")
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_patchpilot.db"

# Override settings DATABASE_URL for tests
from app.core.config import settings
settings.DATABASE_URL = TEST_DATABASE_URL

from app.core.database import Base, get_db, init_db, engine, AsyncSessionLocal
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def initialize_test_database():
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass

    await init_db()
    yield
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass


@pytest_asyncio.fixture
async def client(initialize_test_database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
