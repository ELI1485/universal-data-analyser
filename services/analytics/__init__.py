"""Analytics services package for statistical analysis, trends, and KPIs."""

from services.analytics.descriptive_statistics import calculer
from services.analytics.trend_analysis import analyser_tendances
from services.analytics.kpi_engine import calculer_kpis
from services.analytics.analytics_service import analyser

__all__ = ["calculer", "analyser_tendances", "calculer_kpis", "analyser"]
