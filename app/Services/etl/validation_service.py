"""Validation service for verifying DataFrame quality before processing.

Checks that the data is not empty, has valid column headers, contains
at least one numeric column, and is not entirely NaN.
"""

import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)


def valider(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate a DataFrame for processing readiness.

    Performs the following checks:
    - DataFrame is not empty (has rows)
    - Has column headers (not default integer indices)
    - Contains at least one numeric column
    - Is not entirely NaN values
    - Column names are reasonable (not excessively long or all identical)

    Args:
        df: The pandas DataFrame to validate.

    Returns:
        A tuple of (is_valid, error_messages).
        If valid: (True, [])
        If invalid: (False, [list of error messages])
    """
    errors: list[str] = []

    # Check 1: DataFrame is not empty
    if df.empty:
        errors.append("Le fichier ne contient aucune donnée (0 lignes).")
        logger.warning("Validation échouée: DataFrame vide")
        return False, errors

    if len(df) == 0:
        errors.append("Le fichier ne contient aucune ligne de données.")
        logger.warning("Validation échouée: 0 lignes")
        return False, errors

    # Check 2: Has proper column headers
    columns = df.columns.tolist()
    if all(isinstance(col, int) for col in columns):
        errors.append(
            "Le fichier ne semble pas avoir d'en-têtes de colonnes. "
            "La première ligne doit contenir les noms des colonnes."
        )
        logger.warning("Validation échouée: pas d'en-têtes de colonnes")

    # Check 3: Log if no numeric columns (but don't block — categorical data is valid)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "string", "bool"]).columns.tolist()
    if len(numeric_cols) == 0 and len(categorical_cols) > 0:
        logger.info(
            "Le fichier ne contient aucune colonne numérique mais contient %d colonnes catégoriques. "
            "L'analyse catégorielle sera utilisée.",
            len(categorical_cols),
        )
    elif len(numeric_cols) == 0 and len(categorical_cols) == 0:
        errors.append(
            "Le fichier ne contient aucune colonne exploitable "
            "(ni numérique ni catégorielle)."
        )
        logger.warning("Validation échouée: aucune colonne exploitable")

    # Check 4: Not all NaN
    if df.isna().all().all():
        errors.append(
            "Toutes les valeurs du fichier sont manquantes (NaN). "
            "Le fichier doit contenir des données valides."
        )
        logger.warning("Validation échouée: toutes les valeurs sont NaN")

    # Check 5: Reasonable column names
    for col in columns:
        col_str = str(col)
        if len(col_str) > 200:
            errors.append(
                f"Le nom de colonne '{col_str[:50]}...' est trop long "
                f"(plus de 200 caractères)."
            )
            logger.warning("Validation: nom de colonne trop long")
            break

    # Check for all identical column names
    if len(set(str(c) for c in columns)) == 1 and len(columns) > 1:
        errors.append(
            "Toutes les colonnes ont le même nom. "
            "Chaque colonne doit avoir un nom unique."
        )
        logger.warning("Validation: tous les noms de colonnes identiques")

    # Check minimum data quality: at least 10% non-null values
    non_null_ratio = df.notna().sum().sum() / (len(df) * len(df.columns))
    if non_null_ratio < 0.1:
        errors.append(
            f"Le fichier contient plus de 90% de valeurs manquantes "
            f"({(1 - non_null_ratio) * 100:.1f}% de NaN). "
            f"Qualité insuffisante pour l'analyse."
        )
        logger.warning(
            "Validation: taux de valeurs manquantes trop élevé (%.1f%%)",
            (1 - non_null_ratio) * 100,
        )

    is_valid = len(errors) == 0
    if is_valid:
        logger.info(
            "Validation réussie: %d lignes, %d colonnes, %d numériques",
            len(df),
            len(df.columns),
            len(numeric_cols),
        )
    else:
        logger.warning("Validation échouée avec %d erreur(s)", len(errors))

    return is_valid, errors
