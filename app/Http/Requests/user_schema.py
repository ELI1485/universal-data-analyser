"""Pydantic schemas for user-related operations.

Provides request/response validation for login, signup,
and user management endpoints.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Schema for user login requests.

    Attributes:
        email: The user's email address (validated format).
        password: The plain-text password (min 6 characters).
    """

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class SignupRequest(BaseModel):
    """Schema for user signup requests.

    Attributes:
        nom: The user's full name (2-100 chars).
        email: The user's email address (validated format).
        password: Password meeting strength requirements.
    """

    nom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password has uppercase, lowercase, digit, and special char."""
        if not re.search(r"[A-Z]", v):
            raise ValueError(
                "Le mot de passe doit contenir au moins une lettre majuscule."
            )
        if not re.search(r"[a-z]", v):
            raise ValueError(
                "Le mot de passe doit contenir au moins une lettre minuscule."
            )
        if not re.search(r"[0-9]", v):
            raise ValueError(
                "Le mot de passe doit contenir au moins un chiffre."
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError(
                "Le mot de passe doit contenir au moins un caractère spécial."
            )
        return v

    @field_validator("nom")
    @classmethod
    def validate_nom(cls, v: str) -> str:
        """Strip whitespace and ensure name is not blank."""
        v = v.strip()
        if not v:
            raise ValueError("Le nom ne peut pas être vide.")
        return v


class UserResponse(BaseModel):
    """Schema for user information responses.

    Attributes:
        id: The user's unique ID.
        nom: The user's full name.
        email: The user's email.
        role: The user's role.
        statut: The account status.
        cree_le: Account creation timestamp.
        derniere_conn: Last login timestamp.
    """

    id: int
    nom: str
    email: str
    role: str
    statut: str
    cree_le: Optional[datetime] = None
    derniere_conn: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Schema for updating a user's profile.

    All fields are optional — only provided fields are updated.

    Attributes:
        nom: New full name.
        email: New email address.
        role: New role (admin or analyste).
        statut: New account status.
    """

    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    statut: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Ensure role is admin or analyste."""
        if v is not None and v not in ("admin", "analyste"):
            raise ValueError(
                "Le rôle doit être 'admin' ou 'analyste'."
            )
        return v

    @field_validator("statut")
    @classmethod
    def validate_statut(cls, v: Optional[str]) -> Optional[str]:
        """Ensure status is valid."""
        if v is not None and v not in ("actif", "inactif", "suspendu"):
            raise ValueError(
                "Le statut doit être 'actif', 'inactif' ou 'suspendu'."
            )
        return v


class TokenResponse(BaseModel):
    """Schema for authentication token responses.

    Attributes:
        token: The JWT token string.
        user_id: The authenticated user's ID.
        role: The user's role.
        nom: The user's display name.
    """

    token: str
    user_id: int
    role: str
    nom: str
