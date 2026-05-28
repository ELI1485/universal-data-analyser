"""AuditLog ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class AuditLog(Base):
    """SQLAlchemy model for the 'audit_logs' table.

    Attributes:
        id: Primary key, auto-incremented.
        user_id: Foreign key to the user (nullable for system events).
        action: Description of the action performed.
        entite: Entity type affected (e.g., 'dataset', 'user').
        entite_id: ID of the affected entity.
        statut: Outcome status ('succes' or 'erreur').
        message: Additional message or error details.
        ip_address: IP address of the client.
        horodatage: Timestamp of the event.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    entite: Mapped[str] = mapped_column(String(100), nullable=False)
    entite_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    statut: Mapped[str] = mapped_column(
        Enum("succes", "erreur", name="audit_statut_enum"), nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    horodatage: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"statut='{self.statut}')>"
        )
