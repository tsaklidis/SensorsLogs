#!/usr/bin/env python3
"""
Generate a secure token for API authentication.

Usage:
    python generate_token.py
"""

import secrets

def generate_token(length=32):
    """
    Generate a secure URL-safe token.

    Args:
        length: Number of bytes (default 32, produces ~43 characters in base64)

    Returns:
        A secure random token string
    """
    return secrets.token_urlsafe(length)

if __name__ == "__main__":
    token = generate_token()
    print("=" * 60)
    print("Generated Secure Token")
    print("=" * 60)
    print(f"\n{token}\n")
    print("=" * 60)
    print("\nAdd this to your .env file:")
    print(f"APP_API_TOKEN={token}")
    print("=" * 60)
    print("\nUse in requests:")
    print(f"Authorization: Bearer {token}")
    print("=" * 60)

