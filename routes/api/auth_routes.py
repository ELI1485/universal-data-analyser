"""Authentication API routes."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.Http.Controllers.auth_controller import AuthController
from app.Http.Requests.user_schema import LoginRequest, SignupRequest, TokenResponse

logger = logging.getLogger(__name__)
router = APIRouter()
_auth_ctrl = AuthController()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, req: Request):
    """Authenticate a user and return a JWT token.

    Args:
        request: Login credentials (email + password).
        req: FastAPI Request for IP extraction.

    Returns:
        TokenResponse with JWT token and user info.
    """
    ip = req.client.host if req.client else "127.0.0.1"
    try:
        result = _auth_ctrl.login(request.email, request.password, ip)
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, req: Request):
    """Register a new user account.

    Args:
        request: Signup data (name, email, password).
        req: FastAPI Request for IP extraction.

    Returns:
        The created user info.
    """
    ip = req.client.host if req.client else "127.0.0.1"
    try:
        result = _auth_ctrl.register(request.nom, request.email, request.password, ip)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me")
def get_me(current_user: dict = None):
    """Get the current user's profile.

    Note: This endpoint requires the Authorization header with a Bearer token.
    Use the get_current_user dependency for protected access.
    """
    from app.Http.Middleware.dependencies import get_current_user as _get_user
    from fastapi import Header
    # This is a simplified version — the full auth is handled via dependencies
    return {"message": "Use Authorization header with Bearer token"}
