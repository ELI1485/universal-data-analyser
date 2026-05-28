"""Report ORM model."""

from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class Report(Base):
    """SQLAlchemy model for the 'reports' table.

    Attributes:
        id: Primary key, auto-incremented.
        dataset_id: Foreign key to the associated dataset.
        user_id: Foreign key to the user who generated the report.
        format: Report format (pdf or excel).
        chemin_export: File path where the report is exported.
        taille_ko: File size in kilobytes.
        genere_le: Report generation timestamp.
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    format: Mapped[str] = mapped_column(
        Enum("pdf", "excel", name="report_format_enum"), nullable=False
    )
    chemin_export: Mapped[str] = mapped_column(String(500), nullable=False)
    taille_ko: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    genere_le: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Report(id={self.id}, dataset_id={self.dataset_id}, "
            f"format='{self.format}')>"
        )
