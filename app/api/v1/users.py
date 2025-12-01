"""
User management endpoints.

Handles user information retrieval.
"""
import logging
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.databases.models import User
from app.databases.serializers import UserRead


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return current_user

