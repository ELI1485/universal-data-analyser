"""Analytics API routes for running and retrieving analyses."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.Http.Middleware.dependencies import get_current_user
from app.Http.Controllers.analytics_controller import AnalyticsController

logger = logging.getLogger(__name__)
router = APIRouter()
_analytics_ctrl = AnalyticsController()


@router.post("/{dataset_id}/run")
def run_analysis(
    dataset_id: int, current_user: dict = Depends(get_current_user)
):
    """Execute full analytics and anomaly detection on a dataset.

    Runs descriptive statistics, trend analysis, KPIs, clustering,
    correlation analysis, and anomaly detection (Z-Score, IQR,
    Isolation Forest) in parallel.

    Args:
        dataset_id: The dataset to analyze.
        current_user: Authenticated user info.

    Returns:
        Combined analytics and anomaly detection results.
    """
    try:
        results = _analytics_ctrl.executer_analyses(
            dataset_id, current_user["user_id"]
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse: {str(e)}",
        )


@router.get("/{dataset_id}")
def get_results(
    dataset_id: int, current_user: dict = Depends(get_current_user)
):
    """Retrieve existing analysis results for a dataset.

    Args:
        dataset_id: The dataset ID.
        current_user: Authenticated user info.

    Returns:
        Stored analytics and anomaly data.
    """
    try:
        results = _analytics_ctrl.obtenir_resultats(
            dataset_id, current_user["user_id"], current_user["role"]
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
