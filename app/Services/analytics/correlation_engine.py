"""Correlation analysis engine for advanced relationship discovery.

Provides correlation matrix computation, top correlated pairs,
multicollinearity detection, and group-level correlations.
"""

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculer_correlations(df: pd.DataFrame, top_n: int = 10) -> dict[str, Any]:
    """Calculate a full correlation analysis on the DataFrame.

    Computes:
    - The full Pearson correlation matrix for all numeric columns
    - Top N most correlated pairs (absolute value, excluding self-correlations)
    - Top N most negatively correlated pairs
    - Summary statistics about correlation strength distribution

    Args:
        df: The DataFrame to analyze.
        top_n: Number of top pairs to return.

    Returns:
        A dictionary with keys:
        - 'matrice': correlation matrix as nested dict
        - 'top_paires_positives': strongest positive correlations
        - 'top_paires_negatives': strongest negative correlations
        - 'distribution': distribution of correlation strengths
        - 'nb_colonnes_numeriques': count of numeric columns analyzed
    """
    numeric_df = df.select_dtypes(include=["number"])

    if len(numeric_df.columns) < 2:
        logger.info("Moins de 2 colonnes numériques, corrélations non applicables.")
        return {
            "matrice": {},
            "top_paires_positives": [],
            "top_paires_negatives": [],
            "distribution": {},
            "nb_colonnes_numeriques": len(numeric_df.columns),
            "message": "Moins de 2 colonnes numériques disponibles.",
        }

    corr_matrix = numeric_df.corr()

    # Extract all unique pairs with their correlation values
    pairs = []
    cols = corr_matrix.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr_matrix.iloc[i, j]
            if not np.isnan(val):
                pairs.append({
                    "col1": cols[i],
                    "col2": cols[j],
                    "correlation": round(float(val), 4),
                    "abs_correlation": round(abs(float(val)), 4),
                    "force": _categoriser_force(abs(float(val))),
                })

    # Sort by absolute value
    pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)

    # Top positive correlations
    top_positives = [
        p for p in pairs if p["correlation"] > 0
    ][:top_n]

    # Top negative correlations
    top_negatives = sorted(
        [p for p in pairs if p["correlation"] < 0],
        key=lambda x: x["correlation"],
    )[:top_n]

    # Distribution of correlation strengths
    distribution = _calculer_distribution(pairs)

    # Convert matrix to serializable format
    matrice_dict = {}
    for col in corr_matrix.columns:
        matrice_dict[col] = {
            other_col: round(float(corr_matrix.loc[col, other_col]), 4)
            for other_col in corr_matrix.columns
        }

    result = {
        "matrice": matrice_dict,
        "top_paires_positives": top_positives,
        "top_paires_negatives": top_negatives,
        "toutes_paires": pairs,
        "distribution": distribution,
        "nb_colonnes_numeriques": len(numeric_df.columns),
    }

    logger.info(
        "Analyse de corrélation terminée: %d paires analysées, "
        "top positive=%.3f, top negative=%.3f",
        len(pairs),
        top_positives[0]["correlation"] if top_positives else 0,
        top_negatives[0]["correlation"] if top_negatives else 0,
    )

    return result


def detecter_multicollinearite(
    df: pd.DataFrame, seuil: float = 0.9
) -> list[dict[str, Any]]:
    """Detect multicollinearity — pairs with |correlation| >= seuil.

    This is useful for ML preprocessing: highly correlated features
    may cause instability in regression models.

    Args:
        df: The DataFrame to check.
        seuil: Threshold for flagging (default: 0.9).

    Returns:
        A list of dicts with col1, col2, correlation, and recommendation.
    """
    numeric_df = df.select_dtypes(include=["number"])

    if len(numeric_df.columns) < 2:
        return []

    corr_matrix = numeric_df.corr()
    problematic_pairs = []
    cols = corr_matrix.columns.tolist()

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr_matrix.iloc[i, j]
            if not np.isnan(val) and abs(val) >= seuil:
                problematic_pairs.append({
                    "col1": cols[i],
                    "col2": cols[j],
                    "correlation": round(float(val), 4),
                    "abs_correlation": round(abs(float(val)), 4),
                    "recommandation": (
                        f"Envisagez de supprimer '{cols[j]}' car elle est "
                        f"fortement corrélée ({val:.3f}) avec '{cols[i]}'."
                    ),
                })

    problematic_pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)

    logger.info(
        "Multicolinéarité: %d paires détectées (seuil=%.2f)",
        len(problematic_pairs),
        seuil,
    )

    return problematic_pairs


def correlation_par_groupe(
    df: pd.DataFrame, col_groupe: str, top_n: int = 5
) -> dict[str, list[dict]]:
    """Compute correlations within groups defined by a categorical column.

    Useful for discovering relationships that only exist within
    certain segments (e.g., correlation of sales vs. marketing
    spending differs by region).

    Args:
        df: The DataFrame to analyze.
        col_groupe: The categorical column to group by.
        top_n: Number of top pairs per group.

    Returns:
        A dict mapping each group value to its top correlated pairs.
    """
    if col_groupe not in df.columns:
        logger.warning("Colonne de groupe '%s' introuvable.", col_groupe)
        return {}

    result = {}
    groups = df[col_groupe].dropna().unique()

    for group_val in groups:
        group_df = df[df[col_groupe] == group_val]

        if len(group_df) < 5:
            continue

        corr_result = calculer_correlations(group_df, top_n=top_n)
        top_pairs = corr_result.get("top_paires_positives", [])

        result[str(group_val)] = top_pairs

    logger.info(
        "Corrélations par groupe (%s): %d groupes analysés",
        col_groupe,
        len(result),
    )

    return result


def _categoriser_force(abs_val: float) -> str:
    """Categorize a correlation's strength.

    Args:
        abs_val: Absolute correlation value.

    Returns:
        A French-language strength category.
    """
    if abs_val >= 0.9:
        return "Très forte"
    elif abs_val >= 0.7:
        return "Forte"
    elif abs_val >= 0.5:
        return "Modérée"
    elif abs_val >= 0.3:
        return "Faible"
    else:
        return "Très faible"


def _calculer_distribution(pairs: list[dict]) -> dict[str, int]:
    """Calculate the distribution of correlation strengths.

    Args:
        pairs: List of pair dicts with 'abs_correlation' key.

    Returns:
        A dict mapping strength categories to counts.
    """
    distribution = {
        "Très forte (≥0.9)": 0,
        "Forte (0.7-0.9)": 0,
        "Modérée (0.5-0.7)": 0,
        "Faible (0.3-0.5)": 0,
        "Très faible (<0.3)": 0,
    }

    for p in pairs:
        abs_val = p["abs_correlation"]
        if abs_val >= 0.9:
            distribution["Très forte (≥0.9)"] += 1
        elif abs_val >= 0.7:
            distribution["Forte (0.7-0.9)"] += 1
        elif abs_val >= 0.5:
            distribution["Modérée (0.5-0.7)"] += 1
        elif abs_val >= 0.3:
            distribution["Faible (0.3-0.5)"] += 1
        else:
            distribution["Très faible (<0.3)"] += 1

    return distribution
