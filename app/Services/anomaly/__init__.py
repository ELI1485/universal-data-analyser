"""Anomaly detection services package."""

from app.Services.anomaly.zscore_detector import detecter as detecter_zscore
from app.Services.anomaly.iqr_detector import detecter as detecter_iqr
from app.Services.anomaly.isolation_detector import detecter as detecter_isolation
from app.Services.anomaly.anomaly_service import detecter_toutes

__all__ = ["detecter_zscore", "detecter_iqr", "detecter_isolation", "detecter_toutes"]
