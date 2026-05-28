"""Trend analysis service for detecting temporal patterns.

Detects date columns, computes rolling averages, and analyzes
row-over-row or month-over-month trends for numeric columns.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def analyser_tendances(df: pd.DataFrame) -> dict:
    """Analyze trends in the DataFrame.

    Detects date columns, computes rolling averages, and calculates
    row-over-row or month-over-month trends for numeric columns.

    Args:
        df: The pandas DataFrame to analyze.

    Returns:
        A dictionary with trend information per column:
        - 'tendance_globale': overall direction (hausse/baisse/stable)
        - 'variation_pct': percentage change from first to last
        - 'moyenne_mobile': rolling average values (last 10 points)
        - 'direction': trend direction string
    """
    result: dict = {
        "date_column": None,
        "tendances": {},
        "resume": {},
    }

    # Find date columns
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        logger.info("Aucune colonne numérique pour l'analyse de tendances.")
        return result

    # Sort by date if available
    df_sorted = df.copy()
    if date_cols:
        result["date_column"] = date_cols[0]
        df_sorted = df_sorted.sort_values(by=date_cols[0]).reset_index(drop=True)
    else:
        df_sorted = df_sorted.reset_index(drop=True)

    # Analyze each numeric column
    for col in numeric_cols:
        col_data = df_sorted[col].dropna()

        if len(col_data) < 3:
            result["tendances"][col] = {
                "tendance_globale": "insuffisant",
                "variation_pct": 0.0,
                "direction": "Données insuffisantes",
                "moyenne_mobile": [],
            }
            continue

        # Compute rolling average (window = min(10, len/5))
        window = max(3, min(10, len(col_data) // 5))
        rolling_avg = col_data.rolling(window=window, min_periods=1).mean()

        # Overall trend: compare first and last rolling average
        first_val = rolling_avg.iloc[:window].mean()
        last_val = rolling_avg.iloc[-window:].mean()

        if first_val != 0:
            variation_pct = ((last_val - first_val) / abs(first_val)) * 100
        else:
            variation_pct = 0.0 if last_val == 0 else 100.0

        # Determine direction
        if variation_pct > 5:
            direction = "hausse"
            direction_text = f"Tendance à la hausse (+{variation_pct:.1f}%)"
        elif variation_pct < -5:
            direction = "baisse"
            direction_text = f"Tendance à la baisse ({variation_pct:.1f}%)"
        else:
            direction = "stable"
            direction_text = f"Tendance stable ({variation_pct:+.1f}%)"

        # Month-over-month analysis if date column exists
        mom_analysis = {}
        if date_cols:
            try:
                date_col = date_cols[0]
                df_temp = df_sorted[[date_col, col]].dropna()
                if len(df_temp) > 0:
                    df_temp = df_temp.set_index(date_col)
                    monthly = df_temp[col].resample("ME").mean()
                    if len(monthly) >= 2:
                        mom_changes = monthly.pct_change().dropna()
                        mom_analysis = {
                            "mois_analyses": len(monthly),
                            "variation_moyenne_mensuelle": round(
                                float(mom_changes.mean() * 100), 2
                            ),
                            "meilleur_mois": str(monthly.idxmax()),
                            "pire_mois": str(monthly.idxmin()),
                        }
            except Exception as e:
                logger.debug(
                    "Analyse mensuelle échouée pour '%s': %s", col, e
                )

        # Get last 10 rolling average points for charts
        last_points = rolling_avg.tail(10).tolist()
        last_points = [round(float(v), 4) for v in last_points if not np.isnan(v)]

        result["tendances"][col] = {
            "tendance_globale": direction,
            "variation_pct": round(float(variation_pct), 2),
            "direction": direction_text,
            "moyenne_mobile": last_points,
            "window_size": window,
            "analyse_mensuelle": mom_analysis,
        }

    # Summary
    directions = [t["tendance_globale"] for t in result["tendances"].values()]
    result["resume"] = {
        "colonnes_analysees": len(numeric_cols),
        "en_hausse": directions.count("hausse"),
        "en_baisse": directions.count("baisse"),
        "stables": directions.count("stable"),
        "insuffisantes": directions.count("insuffisant"),
    }

    logger.info(
        "Analyse de tendances terminée: %d colonnes (%d hausse, %d baisse, %d stable)",
        len(numeric_cols),
        result["resume"]["en_hausse"],
        result["resume"]["en_baisse"],
        result["resume"]["stables"],
    )

    return result
