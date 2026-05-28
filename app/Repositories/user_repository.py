"""User repository for database operations on the users table."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.connection import get_db
from app.Models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository handling all CRUD operations for User entities."""

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by their primary key ID.

        Args:
            user_id: The user's ID.

        Returns:
            The User object or None if not found.
        """
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                db.expunge(user)
            return user

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by their email address.

        Args:
            email: The email to search for.

        Returns:
            The User object or None if not found.
        """
        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.expunge(user)
            return user

    def find_all(self) -> list[User]:
        """Retrieve all users from the database.

        Returns:
            A list of all User objects.
        """
        with get_db() as db:
            users = db.query(User).all()
            for user in users:
                db.expunge(user)
            return users

    def create(self, nom: str, email: str, hashed_password: str, role: str) -> User:
        """Create a new user in the database.

        Args:
            nom: The user's full name.
            email: The user's email address.
            hashed_password: The bcrypt-hashed password.
            role: The user's role ('admin' or 'analyste').

        Returns:
            The newly created User object.
        """
        with get_db() as db:
            user = User(
                nom=nom,
                email=email,
                mot_de_passe=hashed_password,
                role=role,
                statut="actif",
                tentatives_echec=0,
            )
            db.add(user)
            db.flush()
            db.expunge(user)
            logger.info("Utilisateur créé: %s (%s)", email, role)
            return user

    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update a user's fields.

        Args:
            user_id: The user's ID.
            **kwargs: Field-value pairs to update.

        Returns:
            The updated User object or None if not found.
        """
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning("Utilisateur non trouvé pour mise à jour: ID=%d", user_id)
                return None
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.flush()
            db.expunge(user)
            logger.info("Utilisateur mis à jour: ID=%d", user_id)
            return user

    def delete(self, user_id: int) -> bool:
        """Delete a user from the database.

        Args:
            user_id: The user's ID.

        Returns:
            True if deleted, False if user not found.
        """
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning("Utilisateur non trouvé pour suppression: ID=%d", user_id)
                return False
            db.delete(user)
            logger.info("Utilisateur supprimé: ID=%d", user_id)
            return True

    def increment_failed_attempts(self, user_id: int) -> None:
        """Increment the failed login attempts counter for a user.

        Args:
            user_id: The user's ID.
        """
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.tentatives_echec = (user.tentatives_echec or 0) + 1
                logger.info(
                    "Tentatives échouées incrémentées pour user ID=%d: %d",
                    user_id,
                    user.tentatives_echec,
                )

    def reset_failed_attempts(self, user_id: int) -> None:
        """Reset the failed login attempts counter to zero.

        Args:
            user_id: The user's ID.
        """
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.tentatives_echec = 0
                logger.info("Tentatives échouées réinitialisées pour user ID=%d", user_id)

    def update_last_login(self, user_id: int) -> None:
        """Update the last login timestamp to now.

        Args:
            user_id: The user's ID.
        """
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.derniere_conn = datetime.utcnow()
                logger.info("Dernière connexion mise à jour pour user ID=%d", user_id)
