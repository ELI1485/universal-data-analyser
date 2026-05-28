"""Anomaly ORM model."""

from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class Anomaly(Base):
    """SQLAlchemy model for the 'anomalies' table.

    Attributes:
        id: Primary key, auto-incremented.
        dataset_id: Foreign key to the associated dataset.
        algorithme: Detection algorithm used.
        score: Anomaly score value.
        type: Type/description of the anomaly.
        ligne: Row number where the anomaly was found.
        colonne: Column name where the anomaly was found.
        detectee_le: Timestamp when the anomaly was detected.
    """

    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasets.id"), nullable=False
    )
    algorithme: Mapped[str] = mapped_column(
        Enum("zscore", "iqr", "isolation_forest", name="anomaly_algo_enum"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    ligne: Mapped[int] = mapped_column(Integer, nullable=False)
    colonne: Mapped[str] = mapped_column(String(100), nullable=False)
    detectee_le: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Anomaly(id={self.id}, dataset_id={self.dataset_id}, "
            f"algorithme='{self.algorithme}', ligne={self.ligne})>"
        )
