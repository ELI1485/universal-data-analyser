"""Integration tests for the full ETL pipeline."""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from services.etl.ingestion_service import lire_fichier
from services.etl.validation_service import valider
from services.etl.cleaning_service import nettoyer


class TestETLPipelineIntegration:
    """Integration tests for the ETL pipeline end-to-end."""

    def test_full_csv_pipeline(self):
        """Test full pipeline: ingest CSV → validate → clean."""
        # Create a temp CSV file
        df_original = pd.DataFrame({
            "Name": ["Alice", "Bob", "Charlie", "Alice", "Bob", None],
            "Age": [25, 30, np.nan, 25, 30, 40],
            "Salary": [50000, 60000, 70000, 50000, 60000, 80000],
            "City": ["Paris", "Lyon", None, "Paris", "Lyon", "Marseille"],
        })

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            df_original.to_csv(f, index=False)
            temp_path = f.name

        try:
            # Step 1: Ingest
            df_ingested = lire_fichier(temp_path)
            assert len(df_ingested) == 6
            assert len(df_ingested.columns) == 4

            # Step 2: Validate
            is_valid, errors = valider(df_ingested)
            assert is_valid is True
            assert errors == []

            # Step 3: Clean
            df_cleaned, quality_report = nettoyer(df_ingested)

            # Verify duplicates removed (Alice/Bob pair is duplicate)
            assert quality_report["doublons_supprimes"] == 2
            assert len(df_cleaned) == 4

            # Verify nulls filled
            assert df_cleaned.isna().sum().sum() == 0
            assert quality_report["valeurs_nulles_remplies"] >= 2

            # Verify column names normalized
            assert "name" in df_cleaned.columns
            assert "age" in df_cleaned.columns
            assert "salary" in df_cleaned.columns

        finally:
            os.unlink(temp_path)

    def test_invalid_file_raises(self):
        """Non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            lire_fichier("/nonexistent/file.csv")

    def test_empty_csv_raises(self):
        """Empty CSV raises appropriate error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(Exception):
                lire_fichier(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validation_rejects_all_nan(self):
        """Validation rejects DataFrame that is entirely NaN."""
        df = pd.DataFrame({"a": [np.nan, np.nan], "b": [np.nan, np.nan]})
        is_valid, errors = valider(df)
        assert is_valid is False
        assert len(errors) > 0

    def test_validation_rejects_no_numeric(self):
        """Validation rejects DataFrame with no numeric columns."""
        df = pd.DataFrame({"x": ["a", "b", "c"], "y": ["d", "e", "f"]})
        is_valid, errors = valider(df)
        assert is_valid is False
        assert any("numérique" in e for e in errors)

    def test_excel_file_ingestion(self):
        """Test ingestion of an Excel file."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_path = f.name
            df.to_excel(temp_path, index=False)

        try:
            result = lire_fichier(temp_path)
            assert len(result) == 3
            assert len(result.columns) == 2
        finally:
            os.unlink(temp_path)
