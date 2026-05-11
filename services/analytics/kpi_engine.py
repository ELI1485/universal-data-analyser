"""KPI engine for computing key performance indicators from a DataFrame.

Calculates dataset-level KPIs including completeness rate, column counts,
correlation matrix, and top correlated pairs.
"""

import logging
from itertools import combinations

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculer_kpis(df: pd.DataFrame) -> dict:
    """Compute key performance indicators for the dataset.

    KPIs computed:
    - total_rows: Total number of rows
    - total_columns: Total number of columns
    - completeness_rate: Percentage of non-null values
    - numeric_columns_count: Number of numeric columns
    - categorical_columns_count: Number of categorical columns
    - correlation_matrix: Correlation matrix for numeric columns
    - top_correlated_pairs: Pairs with correlation > 0.7

    Args:
        df: The pandas DataFrame to analyze.

    Returns:
        A dictionary containing all computed KPIs.
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Basic KPIs
    total_cells = len(df) * len(df.columns)
    non_null_cells = int(df.notna().sum().sum())
    completeness_rate = round((non_null_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

    result = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "completeness_rate": completeness_rate,
        "numeric_columns_count": len(numeric_cols),
        "categorical_columns_count": len(categorical_cols),
        "datetime_columns_count": len(
            df.select_dtypes(include=["datetime64"]).columns
        ),
        "total_null_values": int(df.isna().sum().sum()),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
        "correlation_matrix": {},
        "top_correlated_pairs": [],
    }

    # Correlation matrix (for numeric columns only)
    if len(numeric_cols) >= 2:
        try:
            corr_matrix = df[numeric_cols].corr()

            # Convert to serializable dict
            result["correlation_matrix"] = {
                col: {
                    row: round(float(corr_matrix.loc[row, col]), 4)
                    for row in corr_matrix.index
                }
                for col in corr_matrix.columns
            }

            # Find top correlated pairs (|correlation| > 0.7, excluding self)
            top_pairs = []
            for col1, col2 in combinations(numeric_cols, 2):
                corr_val = corr_matrix.loc[col1, col2]
                if not np.isnan(corr_val) and abs(corr_val) > 0.7:
                    top_pairs.append(
                        {
                            "col1": col1,
                            "col2": col2,
                            "value": round(float(corr_val), 4),
                            "strength": _categorize_correlation(abs(corr_val)),
                        }
                    )

            # Sort by absolute correlation value
            top_pairs.sort(key=lambda x: abs(x["value"]), reverse=True)
            result["top_correlated_pairs"] = top_pairs[:20]  # Limit to top 20

        except Exception as e:
            logger.warning("Erreur calcul matrice de corrélation: %s", e)
            result["correlation_matrix"] = {}
            result["top_correlated_pairs"] = []
    else:
        logger.info("Moins de 2 colonnes numériques, corrélation non calculée.")

    # Per-column completeness
    column_completeness = {}
    for col in df.columns:
        non_null = int(df[col].notna().sum())
        column_completeness[col] = round(non_null / len(df) * 100, 2) if len(df) > 0 else 0.0
    result["column_completeness"] = column_completeness

    logger.info(
        "KPIs calculés: %d lignes, %d colonnes, complétude=%.1f%%",
        result["total_rows"],
        result["total_columns"],
        result["completeness_rate"],
    )

    return result


def _categorize_correlation(abs_value: float) -> str:
    """Categorize the strength of a correlation coefficient.

    Args:
        abs_value: Absolute value of the correlation coefficient.

    Returns:
        A French-language strength description.
    """
    if abs_value >= 0.9:
        return "Très forte"
    elif abs_value >= 0.7:
        return "Forte"
    elif abs_value >= 0.5:
        return "Modérée"
    elif abs_value >= 0.3:
        return "Faible"
    else:
        return "Très faible"
