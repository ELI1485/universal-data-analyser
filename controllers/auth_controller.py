"""Authentication controller handling login, logout, and token verification."""

import logging
from typing import Optional

from services import auth_service
from services.audit_service import log_action
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

_user_repo = UserRepository()


class AuthController:
    """Controller for authentication operations."""

    def login(self, email: str, password: str, ip: str = "127.0.0.1") -> dict:
        """Authenticate a user and return session info.

        Args:
            email: The user's email address.
            password: The plain-text password.
            ip: The client's IP address.

        Returns:
            A dict with token, user_id, role, and nom.

        Raises:
            ValueError: If credentials are invalid.
            PermissionError: If the account is locked/suspended.
        """
        try:
            token = auth_service.login(email, password, ip)
            user_info = auth_service.get_current_user(token)
            user = _user_repo.find_by_id(user_info["user_id"])

            result = {
                "token": token,
                "user_id": user_info["user_id"],
                "role": user_info["role"],
                "nom": user.nom if user else "Utilisateur",
            }
            logger.info("Login réussi pour %s", email)
            return result

        except (ValueError, PermissionError) as e:
            logger.warning("Login échoué pour %s: %s", email, e)
            raise

    def register(self, nom: str, email: str, password: str, ip: str = "127.0.0.1") -> dict:
        """Register a new user.

        Args:
            nom: The user's full name.
            email: The user's email address.
            password: The plain-text password.
            ip: The client's IP address.

        Returns:
            A dict with user info.

        Raises:
            ValueError: If registration fails.
        """
        try:
            result = auth_service.signup(nom, email, password, ip)
            return result
        except ValueError as e:
            raise
        except Exception as e:
            logger.error("Erreur lors de l'inscription: %s", e)
            raise ValueError(f"Erreur lors de l'inscription: {str(e)}")

    def logout(self, token: str, ip: str = "127.0.0.1") -> None:
        """Log the user out and record the audit event.

        Args:
            token: The current JWT token.
            ip: The client's IP address.
        """
        try:
            user_info = auth_service.get_current_user(token)
            log_action(
                user_id=user_info["user_id"],
                action="logout",
                entite="user",
                entite_id=user_info["user_id"],
                statut="succes",
                message="Déconnexion",
                ip=ip,
            )
            logger.info("Logout pour user_id=%d", user_info["user_id"])
        except Exception as e:
            logger.warning("Erreur lors du logout: %s", e)

    def get_current_user(self, token: str) -> dict:
        """Get the current user's information from their token.

        Args:
            token: The JWT token.

        Returns:
            A dict with user_id and role.

        Raises:
            jwt.ExpiredSignatureError: If token expired.
            jwt.InvalidTokenError: If token is invalid.
        """
        return auth_service.get_current_user(token)

    def require_admin(self, token: str) -> dict:
        """Verify that the token holder is an admin.

        Args:
            token: The JWT token.

        Returns:
            The user info dict.

        Raises:
            PermissionError: If the user is not an admin.
        """
        user_info = auth_service.get_current_user(token)
        if user_info["role"] != "admin":
            raise PermissionError(
                "Accès refusé. Cette fonctionnalité nécessite le rôle administrateur."
            )
        return user_info
