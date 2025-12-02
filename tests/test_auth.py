"""
Tests for authentication endpoints.
"""
import asyncio

import pytest
from httpx import AsyncClient

from app.databases.crud import CrudService


# Registration is disabled - users are created by administrators via admin panel
# Tests removed: TestRegister class


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


class TestAccountLockout:
    """Tests for account lockout functionality after failed login attempts."""

    async def test_account_locks_after_max_attempts(self, client: AsyncClient, test_user: dict):
        """Test that account locks after maximum failed login attempts."""
        # Make 5 failed login attempts (default MAX_LOGIN_ATTEMPTS)
        for attempt in range(5):
            response = await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401, f"Attempt {attempt + 1} should fail with 401"

        # 6th attempt should result in lockout
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 423, "Account should be locked (HTTP 423)"
        data = response.json()
        assert "locked" in data["detail"].lower()
        assert "Retry-After" in response.headers

    async def test_lockout_prevents_correct_password(self, client: AsyncClient, test_user: dict):
        """Test that lockout prevents login even with correct password."""
        # Lock the account with failed attempts
        for _ in range(5):
            await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )

        # Try with correct password - should still be locked
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 423
        data = response.json()
        assert "locked" in data["detail"].lower()

    async def test_failed_attempts_tracked_per_user(self, client: AsyncClient, test_user: dict, test_user2: dict):
        """Test that failed attempts are tracked per user, not globally."""
        # Make 3 failed attempts for user 1
        for _ in range(3):
            response = await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401

        # User 2 should still be able to login
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user2["username"],
                "password": test_user2["password"]
            }
        )

        assert response.status_code == 200, "User 2 should be able to login"

        # User 1 should still not be locked (only 3 attempts)
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200, "User 1 should be able to login with correct password"

    async def test_successful_login_resets_counter(self, client: AsyncClient, test_user: dict):
        """Test that successful login resets the failed attempts counter."""
        # Make 2 failed attempts (faster test)
        for _ in range(2):
            response = await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401

        # Successful login should reset counter
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200

        # Now we should be able to make 5 failed attempts again before lockout
        for attempt in range(5):
            response = await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401, f"Attempt {attempt + 1} should fail with 401"

        # 6th attempt should lock
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 423

    async def test_lockout_details_and_nonexistent_user(self, client: AsyncClient, test_user: dict):
        """Test lockout message details and that nonexistent users don't reveal existence."""
        # Lock the account
        for _ in range(5):
            await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )

        # Check lockout message includes duration
        response = await client.post(
            "/api/v1.0/auth/login",
            json={
                "username": test_user["username"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 423
        data = response.json()
        detail = data["detail"].lower()

        # Should mention both "locked" and "minute(s)"
        assert "locked" in detail
        assert "minute" in detail

        # Should have Retry-After header with seconds
        retry_after = response.headers.get("Retry-After")
        assert retry_after is not None
        assert int(retry_after) > 0

        # Test nonexistent user doesn't reveal existence (timing attack protection)
        for _ in range(3):  # Reduced from 6 for speed
            response = await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": "nonexistentuser",
                    "password": "WrongPassword123!"
                }
            )
            # Should always get 401, never 423
            assert response.status_code == 401

    async def test_database_fields_updated_correctly(self, client: AsyncClient, test_user: dict, test_db_session):
        """Test that database fields are updated correctly during lockout."""

        crud = CrudService(test_db_session)

        # Get user before any attempts
        user = await crud.get_user_by_username(test_user["username"])
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.last_failed_login is None

        # Make 3 failed attempts
        for _ in range(3):
            await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )

        # Check counter increased
        await test_db_session.refresh(user)
        assert user.failed_login_attempts == 3
        assert user.last_failed_login is not None
        assert user.locked_until is None  # Not locked yet

        # Lock the account (2 more attempts)
        for _ in range(2):
            await client.post(
                "/api/v1.0/auth/login",
                json={
                    "username": test_user["username"],
                    "password": "WrongPassword123!"
                }
            )

        # Check account is locked
        await test_db_session.refresh(user)
        assert user.failed_login_attempts == 5
        assert user.locked_until is not None
        assert user.is_locked() is True

        # Test manual reset functionality
        await crud.reset_failed_login_attempts(user.id)

        await test_db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.last_failed_login is None
