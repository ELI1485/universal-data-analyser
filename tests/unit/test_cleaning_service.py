"""Unit tests for cleaning_service module."""

import numpy as np
import pandas as pd
import pytest

from app.Services.etl.cleaning_service import nettoyer


class TestNettoyerDuplicates:
    """Tests for duplicate removal."""

    def test_removes_exact_duplicates(self):
        """Exact duplicate rows are removed."""
        df = pd.DataFrame({"a": [1, 2, 2, 3], "b": ["x", "y", "y", "z"]})
        cleaned, report = nettoyer(df)
        assert len(cleaned) == 3
        assert report["doublons_supprimes"] == 1

    def test_no_duplicates_unchanged(self):
        """DataFrame without duplicates stays the same length."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        cleaned, report = nettoyer(df)
        assert len(cleaned) == 3
        assert report["doublons_supprimes"] == 0


class TestNettoyerNullFilling:
    """Tests for null value filling."""

    def test_numeric_nulls_filled_with_median(self):
        """Numeric NaN values are filled with column median."""
        df = pd.DataFrame({"value": [1.0, 2.0, np.nan, 4.0, 5.0]})
        cleaned, report = nettoyer(df)
        # Median of [1, 2, 4, 5] = 3.0
        assert cleaned["value"].iloc[2] == 3.0
        assert report["valeurs_nulles_remplies"] >= 1

    def test_string_nulls_filled_with_inconnu(self):
        """String NaN values are filled with 'Inconnu'."""
        df = pd.DataFrame(
            {"name": ["Alice", None, "Charlie"], "value": [1, 2, 3]}
        )
        cleaned, report = nettoyer(df)
        assert cleaned["name"].iloc[1] == "Inconnu"

    def test_no_nulls_unchanged(self):
        """DataFrame without nulls reports 0 nulls filled."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        cleaned, report = nettoyer(df)
        assert report["valeurs_nulles_remplies"] == 0


class TestNettoyerColumnNormalization:
    """Tests for column name normalization."""

    def test_lowercases_columns(self):
        """Column names are lowercased."""
        df = pd.DataFrame({"NOM": [1], "Age": [2], "SALAIRE": [3]})
        cleaned, report = nettoyer(df)
        assert all(col == col.lower() for col in cleaned.columns)

    def test_replaces_spaces_with_underscores(self):
        """Spaces in column names become underscores."""
        df = pd.DataFrame({"First Name": ["a"], "Last Name": ["b"]})
        cleaned, report = nettoyer(df)
        assert "first_name" in cleaned.columns
        assert "last_name" in cleaned.columns

    def test_strips_whitespace(self):
        """Leading/trailing whitespace is stripped from column names."""
        df = pd.DataFrame({" hello ": [1], "world ": [2]})
        cleaned, report = nettoyer(df)
        assert "hello" in cleaned.columns
        assert "world" in cleaned.columns


class TestNettoyerQualityReport:
    """Tests for quality report output."""

    def test_quality_report_has_required_keys(self):
        """Quality report contains all expected keys."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        _, report = nettoyer(df)

        expected_keys = [
            "lignes_initiales",
            "colonnes_initiales",
            "doublons_supprimes",
            "valeurs_nulles_remplies",
            "colonnes_renommees",
            "colonnes_dates_converties",
            "lignes_finales",
            "colonnes_finales",
            "taux_completude",
        ]
        for key in expected_keys:
            assert key in report, f"Missing key: {key}"

    def test_completude_rate_is_percentage(self):
        """Completude rate is between 0 and 100."""
        df = pd.DataFrame({"a": [1, 2, np.nan], "b": ["x", None, "z"]})
        _, report = nettoyer(df)
        assert 0 <= report["taux_completude"] <= 100
