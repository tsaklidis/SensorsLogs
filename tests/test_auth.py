"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for user registration."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_register_duplicate_username(self, client: AsyncClient, test_user: dict):
        """Test registration with duplicate username."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": test_user["username"],
                "email": "different@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: dict):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "differentuser",
                "email": test_user["email"],
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with password too short."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "short"
            }
        )

        assert response.status_code == 422

    async def test_register_short_username(self, client: AsyncClient):
        """Test registration with username too short."""
        response = await client.post(
            "/api/v1.0/auth/register",
            json={
                "username": "ab",
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login."""
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user."""
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh."""

    async def test_refresh_token_success(self, client: AsyncClient, test_user: dict):
        """Test successful token refresh."""
        response = await client.post(
            "/api/v1.0/auth/refresh",
            json={"refresh_token": test_user["refresh_token"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"].count('.') == 2
        assert data["refresh_token"].count('.') == 2

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1.0/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401

    async def test_refresh_access_token_as_refresh(self, client: AsyncClient, test_user: dict):
        """Test using access token as refresh token (should fail)."""
        response = await client.post(
            "/api/v1.0/auth/refresh",
            json={"refresh_token": test_user["access_token"]}
        )

        assert response.status_code == 401


class TestUserMe:
    """Tests for current user endpoint."""

    async def test_get_current_user(self, client: AsyncClient, test_user: dict, auth_headers: dict):
        """Test getting current user information."""
        response = await client.get(
            "/api/v1.0/users/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1.0/users/me")

        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1.0/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

