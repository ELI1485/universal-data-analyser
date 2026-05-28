"""Unit tests for auth_service module."""

import time

import pytest
import jwt

from app.Services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    verify_token,
)
from config.settings import JWT_SECRET_KEY


class TestHashPassword:
    """Tests for hash_password function."""

    def test_hash_returns_string(self):
        """hash_password returns a non-empty string."""
        hashed = hash_password("test123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_different_from_plain(self):
        """Hashed password is different from plain text."""
        plain = "MySecurePassword"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_same_password_different_hashes(self):
        """Same password produces different hashes (unique salts)."""
        h1 = hash_password("same_pass")
        h2 = hash_password("same_pass")
        assert h1 != h2


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_correct_password_returns_true(self):
        """verify_password returns True for correct password."""
        plain = "CorrectPassword123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_wrong_password_returns_false(self):
        """verify_password returns False for wrong password."""
        hashed = hash_password("CorrectPassword123")
        assert verify_password("WrongPassword", hashed) is False

    def test_empty_password_returns_false(self):
        """verify_password returns False for empty password against hash."""
        hashed = hash_password("SomePassword")
        assert verify_password("", hashed) is False


class TestCreateToken:
    """Tests for create_token function."""

    def test_creates_valid_jwt(self):
        """create_token returns a valid JWT string."""
        token = create_token(user_id=1, role="admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_correct_payload(self):
        """Token decodes to contain user_id and role."""
        token = create_token(user_id=42, role="analyste")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        assert payload["user_id"] == 42
        assert payload["role"] == "analyste"
        assert "exp" in payload
        assert "iat" in payload


class TestVerifyToken:
    """Tests for verify_token function."""

    def test_valid_token_decodes(self):
        """verify_token successfully decodes a valid token."""
        token = create_token(user_id=1, role="admin")
        payload = verify_token(token)
        assert payload["user_id"] == 1
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        """verify_token raises ExpiredSignatureError for expired tokens."""
        import datetime

        payload = {
            "user_id": 1,
            "role": "admin",
            "exp": datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
            "iat": datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
        }
        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(expired_token)

    def test_invalid_token_raises(self):
        """verify_token raises InvalidTokenError for tampered tokens."""
        with pytest.raises(jwt.InvalidTokenError):
            verify_token("not.a.valid.token")

    def test_wrong_secret_raises(self):
        """verify_token raises for tokens signed with wrong secret."""
        token = jwt.encode(
            {"user_id": 1, "role": "admin", "exp": 9999999999},
            "wrong_secret",
            algorithm="HS256",
        )
        with pytest.raises(jwt.InvalidTokenError):
            verify_token(token)
