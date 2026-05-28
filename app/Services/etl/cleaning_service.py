"""Cleaning service for data preprocessing and quality improvement.

Handles duplicate removal, missing value imputation, column name
normalization, and date column detection.
"""

import logging
import re
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def nettoyer(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean and preprocess a DataFrame.

    Performs the following operations:
    1. Remove exact duplicate rows
    2. Handle missing values (numeric→median, string→'Inconnu')
    3. Normalize column names (strip, lowercase, spaces→underscores)
    4. Detect and convert date columns

    Args:
        df: The raw pandas DataFrame to clean.

    Returns:
        A tuple of (cleaned_df, quality_report) where quality_report
        contains statistics about the cleaning operations performed.
    """
    quality_report: dict[str, Any] = {
        "lignes_initiales": len(df),
        "colonnes_initiales": len(df.columns),
        "doublons_supprimes": 0,
        "valeurs_nulles_remplies": 0,
        "colonnes_renommees": 0,
        "colonnes_dates_converties": 0,
        "colonnes_originales": df.columns.tolist(),
    }

    # Make a copy to avoid modifying the original
    df_clean = df.copy()

    # Step 1: Remove exact duplicate rows
    df_clean, duplicates_removed = _supprimer_doublons(df_clean)
    quality_report["doublons_supprimes"] = duplicates_removed

    # Step 2: Handle missing values
    df_clean, nulls_filled = _remplir_valeurs_manquantes(df_clean)
    quality_report["valeurs_nulles_remplies"] = nulls_filled

    # Step 3: Normalize column names
    df_clean, columns_renamed = _normaliser_colonnes(df_clean)
    quality_report["colonnes_renommees"] = columns_renamed

    # Step 4: Detect and convert date columns
    df_clean, dates_converted = _convertir_dates(df_clean)
    quality_report["colonnes_dates_converties"] = dates_converted

    # Final stats
    quality_report["lignes_finales"] = len(df_clean)
    quality_report["colonnes_finales"] = len(df_clean.columns)
    quality_report["colonnes_nettoyees"] = df_clean.columns.tolist()
    quality_report["taux_completude"] = round(
        df_clean.notna().sum().sum() / (len(df_clean) * len(df_clean.columns)) * 100, 2
    )

    logger.info(
        "Nettoyage terminé: %d doublons supprimés, %d nulls remplis, "
        "%d colonnes renommées, %d dates converties",
        duplicates_removed,
        nulls_filled,
        columns_renamed,
        dates_converted,
    )

    return df_clean, quality_report


def _supprimer_doublons(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate rows from the DataFrame.

    Args:
        df: The DataFrame to deduplicate.

    Returns:
        A tuple of (deduplicated_df, count_removed).
    """
    initial_count = len(df)
    df_dedup = df.drop_duplicates()
    removed = initial_count - len(df_dedup)

    if removed > 0:
        logger.info("Doublons supprimés: %d lignes", removed)

    return df_dedup, removed


def _remplir_valeurs_manquantes(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Fill missing values based on column type.

    Numeric columns: fill with median.
    String/object columns: fill with 'Inconnu'.

    Args:
        df: The DataFrame with missing values.

    Returns:
        A tuple of (filled_df, total_nulls_filled).
    """
    total_nulls_filled = 0

    # Numeric columns: fill with median
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        null_count = df[col].isna().sum()
        if null_count > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            total_nulls_filled += null_count
            logger.debug(
                "Colonne '%s': %d nulls remplis avec médiane (%.4f)",
                col,
                null_count,
                median_val,
            )

    # String/object columns: fill with 'Inconnu'
    object_cols = df.select_dtypes(include=["object", "category"]).columns
    for col in object_cols:
        null_count = df[col].isna().sum()
        if null_count > 0:
            df[col] = df[col].fillna("Inconnu")
            total_nulls_filled += null_count
            logger.debug(
                "Colonne '%s': %d nulls remplis avec 'Inconnu'", col, null_count
            )

    return df, total_nulls_filled


def _normaliser_colonnes(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Normalize column names: strip, lowercase, replace spaces with underscores.

    Args:
        df: The DataFrame with original column names.

    Returns:
        A tuple of (renamed_df, count_renamed).
    """
    original_cols = df.columns.tolist()
    new_cols = []

    for col in original_cols:
        col_str = str(col)
        # Strip whitespace
        normalized = col_str.strip()
        # Lowercase
        normalized = normalized.lower()
        # Replace spaces and special chars with underscores
        normalized = re.sub(r"[\s\-\.]+", "_", normalized)
        # Remove non-alphanumeric chars except underscores
        normalized = re.sub(r"[^a-z0-9_àâäéèêëïîôùûüÿçœæ]", "", normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip("_")
        # Replace multiple underscores with one
        normalized = re.sub(r"_+", "_", normalized)

        if not normalized:
            normalized = f"colonne_{len(new_cols)}"

        new_cols.append(normalized)

    # Handle duplicate column names after normalization
    seen: dict[str, int] = {}
    final_cols = []
    for col in new_cols:
        if col in seen:
            seen[col] += 1
            final_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            final_cols.append(col)

    # Count how many were actually changed
    count_renamed = sum(
        1 for orig, new in zip(original_cols, final_cols) if str(orig) != new
    )

    df.columns = final_cols
    return df, count_renamed


def _convertir_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Detect and convert potential date columns to datetime type.

    Attempts to parse object columns that look like dates.

    Args:
        df: The DataFrame with potential date columns.

    Returns:
        A tuple of (df_with_dates, count_converted).
    """
    dates_converted = 0
    object_cols = df.select_dtypes(include=["object"]).columns

    for col in object_cols:
        # Skip columns with too many unique values relative to length
        # (likely not dates if >50% unique and >1000 rows)
        if len(df) > 1000 and df[col].nunique() > len(df) * 0.5:
            continue

        # Skip columns that are mostly 'Inconnu' (already filled)
        inconnu_ratio = (df[col] == "Inconnu").sum() / len(df)
        if inconnu_ratio > 0.5:
            continue

        # Try to detect date-like patterns in column name
        date_keywords = ["date", "time", "jour", "mois", "annee", "created", "updated"]
        col_lower = col.lower()
        has_date_keyword = any(kw in col_lower for kw in date_keywords)

        # Sample non-null values for date detection
        sample = df[col].dropna().head(20)
        if len(sample) == 0:
            continue

        # Try parsing
        try:
            parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
            valid_ratio = parsed.notna().sum() / len(parsed)

            # If >80% of sample parses as dates, or column has date keyword
            if valid_ratio > 0.8 or (has_date_keyword and valid_ratio > 0.5):
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                dates_converted += 1
                logger.debug("Colonne '%s' convertie en datetime", col)
        except (ValueError, TypeError, OverflowError):
            continue

    return df, dates_converted
