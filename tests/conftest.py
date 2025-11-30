"""
Pytest configuration and shared fixtures for testing.
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.databases.models import SQLModel, User, Sensor, SensorRecord
from app.databases.manager import get_db
from app.core.config import settings


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Import all models to ensure they're registered
    from app.databases.models import User, Sensor, SensorRecord

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a test user and return user data with tokens."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }

    response = await client.post("/api/v1.0/auth/register", json=user_data)
    assert response.status_code == 201

    tokens = response.json()
    return {
        **user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@pytest.fixture
async def test_user2(client: AsyncClient) -> dict:
    """Create a second test user for multi-user tests."""
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User 2"
    }

    response = await client.post("/api/v1.0/auth/register", json=user_data)
    assert response.status_code == 201

    tokens = response.json()
    return {
        **user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@pytest.fixture
async def auth_headers(test_user: dict) -> dict:
    """Get authorization headers for test user."""
    return {"Authorization": f"Bearer {test_user['access_token']}"}


@pytest.fixture
async def auth_headers2(test_user2: dict) -> dict:
    """Get authorization headers for second test user."""
    return {"Authorization": f"Bearer {test_user2['access_token']}"}


@pytest.fixture
async def test_sensor(client: AsyncClient, auth_headers: dict) -> dict:
    """Create a test sensor and return sensor data."""
    sensor_data = {
        "name": "Test Sensor",
        "location": "Test Location"
    }

    response = await client.post(
        "/api/v1.0/sensors",
        json=sensor_data,
        headers=auth_headers
    )
    assert response.status_code == 201

    return response.json()

