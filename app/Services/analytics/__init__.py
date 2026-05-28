"""Analytics services package for statistical analysis, trends, and KPIs."""

from app.Services.analytics.descriptive_statistics import calculer
from app.Services.analytics.trend_analysis import analyser_tendances
from app.Services.analytics.kpi_engine import calculer_kpis
from app.Services.analytics.analytics_service import analyser

__all__ = ["calculer", "analyser_tendances", "calculer_kpis", "analyser"]
