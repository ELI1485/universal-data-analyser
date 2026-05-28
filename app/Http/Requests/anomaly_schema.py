"""Pydantic schemas for anomaly-related operations.

Provides response validation for anomaly detection results.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnomalyResponse(BaseModel):
    """Schema for a single anomaly result.

    Attributes:
        id: Anomaly primary key.
        dataset_id: Associated dataset ID.
        algorithme: Detection algorithm used (zscore, iqr, isolation_forest).
        score: Anomaly score value.
        type: Type/description of the anomaly.
        ligne: Row number where the anomaly was found.
        colonne: Column name where the anomaly was found.
        detectee_le: Detection timestamp.
    """

    id: int
    dataset_id: int
    algorithme: str
    score: float
    type: str
    ligne: int
    colonne: str
    detectee_le: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnomalyListResponse(BaseModel):
    """Schema for a list of anomalies with summary.

    Attributes:
        anomalies: List of anomaly details.
        total: Total anomaly count.
        resume: Count breakdown by algorithm.
    """

    anomalies: list[AnomalyResponse]
    total: int
    resume: dict[str, int]


class AnomalyDetectionResponse(BaseModel):
    """Schema for anomaly detection execution results.

    Attributes:
        zscore: List of Z-Score anomalies (raw dicts).
        iqr: List of IQR anomalies (raw dicts).
        isolation: List of Isolation Forest anomalies (raw dicts).
        total: Total count across all algorithms.
        saved_count: Number of anomalies persisted to DB.
        resume: Count summary per algorithm.
    """

    zscore: list[dict] = []
    iqr: list[dict] = []
    isolation: list[dict] = []
    total: int = 0
    saved_count: int = 0
    resume: dict[str, int] = {}
