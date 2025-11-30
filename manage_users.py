#!/usr/bin/env python3
"""
User Management CLI Tool

Create and manage users for the Sensors API.
Only administrators should have access to this tool.

Usage:
    python manage_users.py create <username> <email> [--password <password>]
    python manage_users.py list
    python manage_users.py activate <username>
    python manage_users.py deactivate <username>
"""

import asyncio
import sys
import getpass
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings
from app.databases.models import User
from app.databases.serializers import UserCreate
from app.databases.crud import CrudService


async def create_user(username: str, email: str, password: str = None, full_name: str = None):
    """Create a new user."""
    if not password:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords do not match!")
            return False

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        crud = CrudService(session)

        # Check if username exists
        existing = await crud.get_user_by_username(username)
        if existing:
            print(f"❌ Username '{username}' already exists!")
            return False

        # Check if email exists
        existing = await crud.get_user_by_email(email)
        if existing:
            print(f"❌ Email '{email}' already exists!")
            return False

        # Create user
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )

        user = await crud.create_user(user_data)

        print(f"✅ User created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Active: {user.is_active}")
        print()
        print("🔑 Login instructions for user:")
        print(f'   curl -X POST "http://localhost:8000/api/v1.0/auth/login" \\')
        print(f'     -H "Content-Type: application/json" \\')
        print(f"     -d '{{\"username\": \"{user.username}\", \"password\": \"<password>\"}}'")

        return True

    await engine.dispose()


async def list_users():
    """List all users."""
    from sqlmodel import select

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        if not users:
            print("No users found.")
            return

        print(f"\n{'ID':<5} {'Username':<20} {'Email':<30} {'Active':<10} {'Created'}")
        print("-" * 90)

        for user in users:
            active = "✓ Yes" if user.is_active else "✗ No"
            created = user.created_at.strftime("%Y-%m-%d")
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {active:<10} {created}")

        print(f"\nTotal: {len(users)} user(s)")

    await engine.dispose()


async def toggle_user_active(username: str, active: bool):
    """Activate or deactivate a user."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        crud = CrudService(session)
        user = await crud.get_user_by_username(username)

        if not user:
            print(f"❌ User '{username}' not found!")
            return False

        user.is_active = active
        await session.commit()

        status = "activated" if active else "deactivated"
        print(f"✅ User '{username}' has been {status}!")

        return True

    await engine.dispose()


def print_usage():
    """Print usage instructions."""
    print("User Management CLI")
    print()
    print("Usage:")
    print("  python manage_users.py create <username> <email> [--password <pass>] [--full-name <name>]")
    print("  python manage_users.py list")
    print("  python manage_users.py activate <username>")
    print("  python manage_users.py deactivate <username>")
    print()
    print("Examples:")
    print("  python manage_users.py create john john@example.com")
    print("  python manage_users.py create jane jane@example.com --password SecurePass123!")
    print("  python manage_users.py list")
    print("  python manage_users.py deactivate john")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "create":
        if len(sys.argv) < 4:
            print("❌ Error: username and email are required")
            print()
            print_usage()
            sys.exit(1)

        username = sys.argv[2]
        email = sys.argv[3]

        # Parse optional arguments
        password = None
        full_name = None

        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--password" and i + 1 < len(sys.argv):
                password = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--full-name" and i + 1 < len(sys.argv):
                full_name = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        asyncio.run(create_user(username, email, password, full_name))

    elif command == "list":
        asyncio.run(list_users())

    elif command == "activate":
        if len(sys.argv) < 3:
            print("❌ Error: username is required")
            sys.exit(1)

        username = sys.argv[2]
        asyncio.run(toggle_user_active(username, True))

    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("❌ Error: username is required")
            sys.exit(1)

        username = sys.argv[2]
        asyncio.run(toggle_user_active(username, False))

    else:
        print(f"❌ Unknown command: {command}")
        print()
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()

