"""FastAPI dependency injection for authentication and common services."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Header, status

from app.Services import auth_service

logger = logging.getLogger(__name__)


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate the JWT token from the Authorization header.

    Args:
        authorization: The Authorization header value (Bearer <token>).

    Returns:
        A dict with user_id and role.

    Raises:
        HTTPException: If token is missing, expired, or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Support "Bearer <token>" format
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    try:
        user_info = auth_service.get_current_user(token)
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalide ou expiré: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires the current user to be an admin.

    Args:
        current_user: The current user info from token.

    Returns:
        The user info dict if admin.

    Raises:
        HTTPException: If user is not an admin.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Cette fonctionnalité nécessite le rôle administrateur.",
        )
    return current_user
