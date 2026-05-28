"""Unit tests for anomaly detection services."""

import numpy as np
import pandas as pd
import pytest

from app.Services.anomaly.zscore_detector import detecter as detecter_zscore
from app.Services.anomaly.iqr_detector import detecter as detecter_iqr
from app.Services.anomaly.isolation_detector import detecter as detecter_isolation


class TestZScoreDetector:
    """Tests for the Z-Score anomaly detector."""

    def test_detects_known_outlier(self):
        """Z-Score detector flags a known extreme outlier."""
        data = [10, 11, 12, 10, 11, 9, 10, 11, 12, 10, 100]
        df = pd.DataFrame({"value": data})
        anomalies = detecter_zscore(df, seuil=2.0)
        # 100 should be flagged as an anomaly
        flagged_rows = [a["ligne"] for a in anomalies]
        assert 10 in flagged_rows

    def test_returns_list_of_dicts(self):
        """Detector returns a list of dicts with required keys."""
        df = pd.DataFrame({"v": np.random.normal(0, 1, 100)})
        df.loc[0, "v"] = 50  # outlier
        anomalies = detecter_zscore(df, seuil=3.0)
        assert isinstance(anomalies, list)
        if anomalies:
            a = anomalies[0]
            assert "ligne" in a
            assert "colonne" in a
            assert "score" in a
            assert "type" in a
            assert a["type"] == "zscore"

    def test_no_anomalies_in_uniform_data(self):
        """No anomalies detected in perfectly uniform data."""
        df = pd.DataFrame({"value": [5.0] * 100})
        anomalies = detecter_zscore(df, seuil=3.0)
        assert len(anomalies) == 0

    def test_empty_dataframe_returns_empty(self):
        """Empty DataFrame returns no anomalies."""
        df = pd.DataFrame({"value": []})
        anomalies = detecter_zscore(df)
        assert anomalies == []


class TestIQRDetector:
    """Tests for the IQR anomaly detector."""

    def test_detects_values_outside_bounds(self):
        """IQR detector flags values beyond the IQR bounds."""
        # Normal data with one extreme outlier
        data = list(range(1, 101)) + [1000]
        df = pd.DataFrame({"value": data})
        anomalies = detecter_iqr(df, facteur=1.5)
        # 1000 should be detected as an anomaly
        flagged_values = [a["valeur"] for a in anomalies]
        assert 1000.0 in flagged_values

    def test_returns_correct_type(self):
        """All returned anomalies have type='iqr'."""
        df = pd.DataFrame({"v": [1, 2, 3, 4, 5, 100]})
        anomalies = detecter_iqr(df, facteur=1.5)
        for a in anomalies:
            assert a["type"] == "iqr"

    def test_higher_factor_fewer_anomalies(self):
        """Increasing the IQR factor reduces detected anomalies."""
        np.random.seed(42)
        data = np.random.normal(50, 10, 200).tolist() + [200, -100]
        df = pd.DataFrame({"value": data})
        anomalies_15 = detecter_iqr(df, facteur=1.5)
        anomalies_30 = detecter_iqr(df, facteur=3.0)
        assert len(anomalies_30) <= len(anomalies_15)


class TestIsolationDetector:
    """Tests for the Isolation Forest anomaly detector."""

    def test_returns_list_of_dicts_with_keys(self):
        """Isolation Forest returns dicts with required keys."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x": np.random.normal(0, 1, 100),
            "y": np.random.normal(0, 1, 100),
        })
        # Add outliers
        df.loc[0] = [10, 10]
        df.loc[1] = [-10, -10]

        anomalies = detecter_isolation(df, contamination=0.05)
        assert isinstance(anomalies, list)
        if anomalies:
            a = anomalies[0]
            assert "ligne" in a
            assert "colonne" in a
            assert "score" in a
            assert "type" in a
            assert a["type"] == "isolation_forest"

    def test_detects_multivariate_outliers(self):
        """Isolation Forest detects extreme multivariate outliers."""
        np.random.seed(42)
        df = pd.DataFrame({
            "x": np.random.normal(0, 1, 200),
            "y": np.random.normal(0, 1, 200),
        })
        # Inject obvious outliers
        df.loc[0] = [20, 20]
        df.loc[1] = [-20, -20]

        anomalies = detecter_isolation(df, contamination=0.05)
        flagged_rows = [a["ligne"] for a in anomalies]
        assert 0 in flagged_rows or 1 in flagged_rows

    def test_handles_single_numeric_column(self):
        """Handles DataFrame with only one numeric column."""
        df = pd.DataFrame({"x": np.random.normal(0, 1, 50)})
        df.loc[0, "x"] = 100
        anomalies = detecter_isolation(df, contamination=0.1)
        assert isinstance(anomalies, list)

    def test_insufficient_data_returns_empty(self):
        """Returns empty list for very small DataFrames."""
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        anomalies = detecter_isolation(df)
        assert anomalies == []
