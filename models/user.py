"""User ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class User(Base):
    """SQLAlchemy model for the 'users' table.

    Attributes:
        id: Primary key, auto-incremented.
        nom: User's full name.
        email: Unique email address.
        mot_de_passe: Bcrypt-hashed password.
        role: Either 'admin' or 'analyste'.
        statut: Account status ('actif', 'inactif', 'suspendu').
        cree_le: Account creation timestamp.
        derniere_conn: Last login timestamp.
        tentatives_echec: Count of consecutive failed login attempts.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("admin", "analyste", name="user_role_enum"), nullable=False
    )
    statut: Mapped[str] = mapped_column(
        Enum("actif", "inactif", "suspendu", name="user_statut_enum"),
        default="actif",
        server_default="actif",
    )
    cree_le: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    derniere_conn: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )
    tentatives_echec: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
