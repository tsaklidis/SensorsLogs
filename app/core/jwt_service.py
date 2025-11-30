"""
JWT Token Management Service

Handles creation and verification of JWT access and refresh tokens.
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.core.config import settings


class JWTService:
    """Service for creating and verifying JWT tokens."""

    @staticmethod
    def create_access_token(
        user_id: int,
        username: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: The user's ID
            username: The user's username
            additional_claims: Optional additional claims to include

        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "username": username,
            "type": "access",
            "iat": now,  # Issued at
            "exp": expire,  # Expiration time
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return token

    @staticmethod
    def create_refresh_token(user_id: int, username: str) -> str:
        """
        Create a JWT refresh token with longer expiration.

        Args:
            user_id: The user's ID
            username: The user's username

        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": str(user_id),
            "username": username,
            "type": "refresh",
            "iat": now,
            "exp": expire,
        }

        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return token

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and verify a JWT token.

        Args:
            token: The JWT token to decode

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            # Token has expired
            return None
        except jwt.InvalidTokenError:
            # Token is invalid
            return None

    @staticmethod
    def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify an access token and return its payload.

        Args:
            token: The access token to verify

        Returns:
            Token payload if valid access token, None otherwise
        """
        payload = JWTService.decode_token(token)

        if payload is None:
            return None

        # Verify it's an access token
        if payload.get("type") != "access":
            return None

        return payload

    @staticmethod
    def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a refresh token and return its payload.

        Args:
            token: The refresh token to verify

        Returns:
            Token payload if valid refresh token, None otherwise
        """
        payload = JWTService.decode_token(token)

        if payload is None:
            return None

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            return None

        return payload

    @staticmethod
    def get_token_expiration(token: str) -> Optional[datetime]:
        """
        Get the expiration time of a token.

        Args:
            token: The JWT token

        Returns:
            Expiration datetime if valid, None otherwise
        """
        payload = JWTService.decode_token(token)

        if payload is None:
            return None

        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        return None

