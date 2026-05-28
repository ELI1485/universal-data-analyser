"""Pydantic schemas for analytics-related operations.

Provides request/response validation for running analyses,
clustering configuration, and analytics results.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ClusteringConfig(BaseModel):
    """Configuration for K-means clustering.

    Attributes:
        n_clusters: Number of clusters (2-10).
        random_state: Random seed for reproducibility.
    """

    n_clusters: int = Field(default=3, ge=2, le=10)
    random_state: int = Field(default=42)


class AnalyticsRequest(BaseModel):
    """Schema for analytics execution requests.

    Attributes:
        dataset_id: The ID of the dataset to analyze.
        clustering_config: Optional clustering parameters.
        run_anomaly_detection: Whether to include anomaly detection.
    """

    dataset_id: int = Field(..., gt=0)
    clustering_config: Optional[ClusteringConfig] = None
    run_anomaly_detection: bool = Field(default=True)

    @field_validator("dataset_id")
    @classmethod
    def validate_dataset_id(cls, v: int) -> int:
        """Ensure dataset ID is positive."""
        if v <= 0:
            raise ValueError("L'ID du dataset doit être un entier positif.")
        return v


class AnalyticsResponse(BaseModel):
    """Schema for analytics results.

    Attributes:
        dataset_info: Basic dataset metadata.
        statistiques: Descriptive statistics by column.
        tendances: Trend analysis results.
        kpis: Key performance indicators.
        clustering: K-means clustering results.
        correlations: Correlation analysis results.
    """

    dataset_info: dict[str, Any]
    statistiques: Optional[dict[str, Any]] = None
    tendances: Optional[dict[str, Any]] = None
    kpis: Optional[dict[str, Any]] = None
    clustering: Optional[dict[str, Any]] = None
    correlations: Optional[dict[str, Any]] = None
