"""Dataset ORM model."""

from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.base import Base


class Dataset(Base):
    """SQLAlchemy model for the 'datasets' table.

    Attributes:
        id: Primary key, auto-incremented.
        user_id: Foreign key to the user who uploaded the dataset.
        nom: Display name for the dataset.
        chemin_fichier: File path where the dataset is stored.
        format: File format (csv, xlsx, xls).
        nb_lignes: Number of rows in the dataset.
        nb_colonnes: Number of columns in the dataset.
        taille_mo: File size in megabytes.
        colonnes: JSON list of column names.
        statut: Processing status.
        cree_le: Upload timestamp.
    """

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    chemin_fichier: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[str] = mapped_column(
        Enum("csv", "xlsx", "xls", name="dataset_format_enum"), nullable=False
    )
    nb_lignes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nb_colonnes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    taille_mo: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    colonnes: Mapped[dict] = mapped_column(JSON, nullable=True)
    statut: Mapped[str] = mapped_column(
        Enum(
            "importe", "en_traitement", "traite", "erreur",
            name="dataset_statut_enum"
        ),
        default="importe",
        server_default="importe",
    )
    cree_le: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, nom='{self.nom}', statut='{self.statut}')>"
