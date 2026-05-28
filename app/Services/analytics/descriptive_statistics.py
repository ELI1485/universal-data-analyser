"""Descriptive statistics calculation service.

Computes comprehensive statistical measures for both numeric and
categorical (object/category) columns. Numeric columns get the full
distribution suite (mean, median, std, quartiles, skew, kurtosis).
Categorical columns get value-frequency statistics (mode, unique count,
top values) so the engine works on datasets with student names, majors,
filieres, etc.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# How many top categories to keep per categorical column
_TOP_CATEGORIES = 10


def calculer(df: pd.DataFrame) -> dict:
    """Compute descriptive statistics for all columns of any dtype.

    For each column, the engine returns either a numeric stat block or a
    categorical stat block depending on the dtype. Both are stored under
    the same ``"colonnes"`` key so downstream consumers can iterate
    uniformly.

    Args:
        df: The pandas DataFrame to analyze.

    Returns:
        A dictionary with:
        - ``"global"``: overall dataset metrics (row/col counts, dtype distribution,
          counts of numeric/categorical/datetime columns)
        - ``"colonnes"``: per-column stats. Each entry has a ``"_kind"`` key
          set to either ``"numeric"`` or ``"categorical"`` so the UI can
          dispatch.
        - ``"numeric_columns"``: list of numeric column names
        - ``"categorical_columns"``: list of categorical column names
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    result: dict = {
        "global": {
            "nb_lignes": len(df),
            "nb_colonnes": len(df.columns),
            "nb_colonnes_numeriques": len(numeric_cols),
            "nb_colonnes_categorielles": len(categorical_cols),
            "nb_colonnes_datetime": len(datetime_cols),
            "types_colonnes": {},
        },
        "colonnes": {},
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
    }

    # dtype distribution
    type_counts = df.dtypes.value_counts()
    for dtype, count in type_counts.items():
        result["global"]["types_colonnes"][str(dtype)] = int(count)

    # ── Numeric columns ─────────────────────────────────────────
    for col in numeric_cols:
        result["colonnes"][col] = _stats_numeric(df, col)

    # ── Categorical columns ─────────────────────────────────────
    for col in categorical_cols:
        result["colonnes"][col] = _stats_categorical(df, col)

    logger.info(
        "Statistiques descriptives calculees: %d numeriques, %d categorielles",
        len(numeric_cols),
        len(categorical_cols),
    )
    return result


def _stats_numeric(df: pd.DataFrame, col: str) -> dict:
    """Compute the numeric stat block for a column."""
    col_data = df[col].dropna()
    null_count = int(df[col].isna().sum())

    if len(col_data) == 0:
        return {
            "_kind": "numeric",
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
            "null_count": null_count,
        }

    try:
        return {
            "_kind": "numeric",
            "mean": round(float(col_data.mean()), 4),
            "median": round(float(col_data.median()), 4),
            "std": round(float(col_data.std()), 4),
            "min": round(float(col_data.min()), 4),
            "max": round(float(col_data.max()), 4),
            "q25": round(float(col_data.quantile(0.25)), 4),
            "q75": round(float(col_data.quantile(0.75)), 4),
            "skewness": round(float(col_data.skew()), 4),
            "kurtosis": round(float(col_data.kurtosis()), 4),
            "count": int(len(col_data)),
            "null_count": null_count,
        }
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Erreur calcul stats numeriques pour '%s': %s", col, e)
        return {
            "_kind": "numeric",
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
            "null_count": null_count,
            "erreur": str(e),
        }


def _stats_categorical(df: pd.DataFrame, col: str) -> dict:
    """Compute the categorical stat block for a column.

    Captures the dominant categories so the UI can render frequency
    bar charts (e.g., the distribution of students per ``filiere``).
    """
    series = df[col]
    null_count = int(series.isna().sum())
    non_null = series.dropna().astype(str)
    total_non_null = int(len(non_null))

    if total_non_null == 0:
        return {
            "_kind": "categorical",
            "count": 0,
            "null_count": null_count,
            "unique_count": 0,
            "mode": None,
            "mode_frequency": 0,
            "mode_frequency_pct": 0.0,
            "top_values": [],
            "top_values_pct": [],
            "is_dominant": False,
        }

    try:
        value_counts = non_null.value_counts()
        unique_count = int(series.nunique(dropna=True))

        top = value_counts.head(_TOP_CATEGORIES)
        top_values = [
            {"value": str(idx), "count": int(cnt)}
            for idx, cnt in top.items()
        ]
        top_values_pct = [
            {
                "value": str(idx),
                "count": int(cnt),
                "pct": round(float(cnt) / total_non_null * 100, 2),
            }
            for idx, cnt in top.items()
        ]

        mode_value = str(value_counts.index[0])
        mode_freq = int(value_counts.iloc[0])
        mode_pct = round(mode_freq / total_non_null * 100, 2)

        # A column is "dominant" when its mode covers > 30% of values —
        # a useful signal that this categorical column is worth charting.
        is_dominant = mode_pct >= 30.0 and unique_count <= 50

        return {
            "_kind": "categorical",
            "count": total_non_null,
            "null_count": null_count,
            "unique_count": unique_count,
            "mode": mode_value,
            "mode_frequency": mode_freq,
            "mode_frequency_pct": mode_pct,
            "top_values": top_values,
            "top_values_pct": top_values_pct,
            "is_dominant": is_dominant,
        }
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Erreur calcul stats categorielles pour '%s': %s", col, e)
        return {
            "_kind": "categorical",
            "count": total_non_null,
            "null_count": null_count,
            "unique_count": 0,
            "mode": None,
            "mode_frequency": 0,
            "mode_frequency_pct": 0.0,
            "top_values": [],
            "top_values_pct": [],
            "is_dominant": False,
            "erreur": str(e),
        }
