"""Pydantic schemas for dataset-related operations.

Provides request/response validation for file upload,
dataset listing, and dataset metadata.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_FORMATS = {"csv", "xlsx", "xls"}


class DatasetUploadRequest(BaseModel):
    """Schema for dataset upload requests.

    Attributes:
        nom: Display name for the dataset.
        format: File format (validated against allowed list).
    """

    nom: str = Field(..., min_length=1, max_length=255)
    format: Optional[str] = None

    @field_validator("nom")
    @classmethod
    def validate_nom(cls, v: str) -> str:
        """Strip whitespace and ensure name is not blank."""
        v = v.strip()
        if not v:
            raise ValueError("Le nom du dataset ne peut pas être vide.")
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate file format if provided."""
        if v is not None:
            v = v.lower().strip()
            if v not in ALLOWED_FORMATS:
                raise ValueError(
                    f"Format non supporté: '{v}'. "
                    f"Formats acceptés: {', '.join(sorted(ALLOWED_FORMATS))}"
                )
        return v


class DatasetResponse(BaseModel):
    """Schema for dataset information responses.

    Attributes:
        id: Dataset primary key.
        user_id: Owner user ID.
        nom: Display name.
        chemin_fichier: File path on disk.
        format: File format (csv/xlsx/xls).
        nb_lignes: Row count.
        nb_colonnes: Column count.
        taille_mo: File size in MB.
        colonnes: List of column names.
        statut: Processing status.
        cree_le: Upload timestamp.
    """

    id: int
    user_id: int
    nom: str
    chemin_fichier: str
    format: str
    nb_lignes: int
    nb_colonnes: int
    taille_mo: float
    colonnes: Optional[list] = None
    statut: str
    cree_le: Optional[datetime] = None

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for a list of datasets.

    Attributes:
        datasets: List of dataset summaries.
        total: Total count of datasets.
    """

    datasets: list[DatasetResponse]
    total: int
