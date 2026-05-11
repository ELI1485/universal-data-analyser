"""Anomaly detection services package."""

from services.anomaly.zscore_detector import detecter as detecter_zscore
from services.anomaly.iqr_detector import detecter as detecter_iqr
from services.anomaly.isolation_detector import detecter as detecter_isolation
from services.anomaly.anomaly_service import detecter_toutes

__all__ = ["detecter_zscore", "detecter_iqr", "detecter_isolation", "detecter_toutes"]
