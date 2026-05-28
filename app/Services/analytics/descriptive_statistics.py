"""Descriptive statistics calculation service.

Computes comprehensive statistical measures for each numeric column
in a DataFrame: mean, median, std, min, max, quartiles, skewness, kurtosis.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def calculer(df: pd.DataFrame) -> dict:
    """Compute descriptive statistics for all numeric columns.

    For each numeric column computes:
    mean, median, std, min, max, q25, q75, skewness, kurtosis.
    Also computes global stats: nb_lignes, nb_colonnes, types_colonnes.

    Args:
        df: The pandas DataFrame to analyze.

    Returns:
        A dictionary with:
        - 'global': overall dataset metrics
        - 'colonnes': per-column statistics dict
    """
    result = {
        "global": {
            "nb_lignes": len(df),
            "nb_colonnes": len(df.columns),
            "types_colonnes": {},
        },
        "colonnes": {},
    }

    # Column type distribution
    type_counts = df.dtypes.value_counts()
    for dtype, count in type_counts.items():
        result["global"]["types_colonnes"][str(dtype)] = int(count)

    # Statistics for each numeric column
    numeric_cols = df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        col_data = df[col].dropna()

        if len(col_data) == 0:
            result["colonnes"][col] = {
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "q25": None,
                "q75": None,
                "skewness": None,
                "kurtosis": None,
                "count": 0,
                "null_count": int(df[col].isna().sum()),
            }
            continue

        try:
            mean_val = float(col_data.mean())
            median_val = float(col_data.median())
            std_val = float(col_data.std())
            min_val = float(col_data.min())
            max_val = float(col_data.max())
            q25_val = float(col_data.quantile(0.25))
            q75_val = float(col_data.quantile(0.75))
            skewness_val = float(col_data.skew())
            kurtosis_val = float(col_data.kurtosis())

            result["colonnes"][col] = {
                "mean": round(mean_val, 4),
                "median": round(median_val, 4),
                "std": round(std_val, 4),
                "min": round(min_val, 4),
                "max": round(max_val, 4),
                "q25": round(q25_val, 4),
                "q75": round(q75_val, 4),
                "skewness": round(skewness_val, 4),
                "kurtosis": round(kurtosis_val, 4),
                "count": int(len(col_data)),
                "null_count": int(df[col].isna().sum()),
            }
        except Exception as e:
            logger.warning("Erreur calcul stats pour colonne '%s': %s", col, e)
            result["colonnes"][col] = {
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "q25": None,
                "q75": None,
                "skewness": None,
                "kurtosis": None,
                "count": int(len(col_data)),
                "null_count": int(df[col].isna().sum()),
                "erreur": str(e),
            }

    logger.info(
        "Statistiques descriptives calculées pour %d colonnes numériques",
        len(numeric_cols),
    )
    return result
