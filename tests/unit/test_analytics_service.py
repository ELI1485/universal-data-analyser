"""Unit tests for analytics services (descriptive_statistics, kpi_engine)."""

import numpy as np
import pandas as pd
import pytest

from app.Services.analytics.descriptive_statistics import calculer
from app.Services.analytics.kpi_engine import calculer_kpis


class TestDescriptiveStatistics:
    """Tests for the calculer function."""

    def test_returns_expected_keys(self):
        """Result contains 'global' and 'colonnes' keys."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = calculer(df)
        assert "global" in result
        assert "colonnes" in result

    def test_global_has_row_column_counts(self):
        """Global section has correct nb_lignes and nb_colonnes."""
        df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [5, 6, 7, 8]})
        result = calculer(df)
        assert result["global"]["nb_lignes"] == 4
        assert result["global"]["nb_colonnes"] == 2

    def test_column_stats_have_expected_fields(self):
        """Each column's stats dict has mean, median, std, etc."""
        df = pd.DataFrame({"value": [10, 20, 30, 40, 50]})
        result = calculer(df)
        stats = result["colonnes"]["value"]
        expected_fields = ["mean", "median", "std", "min", "max", "q25", "q75", "skewness", "kurtosis"]
        for field in expected_fields:
            assert field in stats, f"Missing field: {field}"

    def test_mean_calculation_correct(self):
        """Mean is calculated correctly."""
        df = pd.DataFrame({"v": [2, 4, 6, 8, 10]})
        result = calculer(df)
        assert result["colonnes"]["v"]["mean"] == 6.0

    def test_empty_numeric_handles_gracefully(self):
        """Non-numeric DataFrame returns empty colonnes."""
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        result = calculer(df)
        assert result["colonnes"] == {}


class TestKPIEngine:
    """Tests for the calculer_kpis function."""

    def test_completeness_rate_calculation(self):
        """Completeness rate is calculated correctly."""
        df = pd.DataFrame({"a": [1, 2, np.nan, 4], "b": [5, np.nan, 7, 8]})
        result = calculer_kpis(df)
        # 6 non-null out of 8 total = 75%
        assert result["completeness_rate"] == 75.0

    def test_full_completeness(self):
        """100% completeness for DataFrame with no nulls."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = calculer_kpis(df)
        assert result["completeness_rate"] == 100.0

    def test_correlation_matrix_shape(self):
        """Correlation matrix has correct number of entries."""
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "z": [7, 8, 9]})
        result = calculer_kpis(df)
        corr = result["correlation_matrix"]
        assert len(corr) == 3  # 3 columns
        assert len(corr["x"]) == 3

    def test_top_correlated_pairs_detected(self):
        """Highly correlated pairs are identified."""
        # x and y are perfectly correlated
        df = pd.DataFrame({"x": range(100), "y": range(100), "z": np.random.randn(100)})
        result = calculer_kpis(df)
        pairs = result["top_correlated_pairs"]
        # x-y should be in top pairs (correlation = 1.0)
        assert any(
            (p["col1"] == "x" and p["col2"] == "y") or
            (p["col1"] == "y" and p["col2"] == "x")
            for p in pairs
        )

    def test_column_counts_correct(self):
        """Numeric and categorical column counts are correct."""
        df = pd.DataFrame({"num1": [1, 2], "num2": [3, 4], "cat": ["a", "b"]})
        result = calculer_kpis(df)
        assert result["numeric_columns_count"] == 2
        assert result["categorical_columns_count"] == 1
