"""Pydantic schemas for report-related operations.

Provides request/response validation for report generation
and report metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ReportFormat(str, Enum):
    """Allowed report formats."""

    PDF = "pdf"
    EXCEL = "excel"


class ReportRequest(BaseModel):
    """Schema for report generation requests.

    Attributes:
        dataset_id: The dataset to report on.
        format: Report output format (pdf or excel).
    """

    dataset_id: int = Field(..., gt=0)
    format: ReportFormat

    @field_validator("dataset_id")
    @classmethod
    def validate_dataset_id(cls, v: int) -> int:
        """Ensure dataset ID is positive."""
        if v <= 0:
            raise ValueError("L'ID du dataset doit être un entier positif.")
        return v


class ReportResponse(BaseModel):
    """Schema for report metadata responses.

    Attributes:
        id: Report primary key.
        dataset_id: Associated dataset ID.
        user_id: User who generated the report.
        format: Report format (pdf or excel).
        chemin_export: File path on disk.
        taille_ko: File size in KB.
        genere_le: Generation timestamp.
    """

    id: int
    dataset_id: int
    user_id: int
    format: str
    chemin_export: str
    taille_ko: float
    genere_le: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for a list of reports.

    Attributes:
        reports: List of report summaries.
        total: Total count.
    """

    reports: list[ReportResponse]
    total: int
