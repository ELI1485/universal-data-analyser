"""IQR (Interquartile Range) anomaly detection.

Detects anomalies by identifying values that fall outside the
[Q1 - factor*IQR, Q3 + factor*IQR] bounds for each numeric column.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def detecter(df: pd.DataFrame, facteur: float = 1.5) -> list[dict]:
    """Detect anomalies using the IQR (Interquartile Range) method.

    For each numeric column, computes Q1, Q3, and IQR, then flags rows
    with values outside [Q1 - facteur*IQR, Q3 + facteur*IQR].

    Args:
        df: The pandas DataFrame to analyze.
        facteur: The IQR multiplier (default: 1.5). Higher values detect
                 fewer, more extreme outliers.

    Returns:
        A list of anomaly dictionaries, each containing:
        - 'ligne': row index
        - 'colonne': column name
        - 'score': distance from the nearest bound (normalized by IQR)
        - 'type': 'iqr'
        - 'valeur': the actual anomalous value
    """
    anomalies: list[dict] = []
    numeric_cols = df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        col_data = df[col].dropna()

        if len(col_data) < 4:
            continue

        # Compute Q1, Q3, and IQR
        q1 = float(col_data.quantile(0.25))
        q3 = float(col_data.quantile(0.75))
        iqr = q3 - q1

        if iqr == 0:
            continue

        # Compute bounds
        lower_bound = q1 - facteur * iqr
        upper_bound = q3 + facteur * iqr

        # Find values outside bounds
        for idx in col_data.index:
            value = float(col_data.loc[idx])

            if value < lower_bound:
                distance = (lower_bound - value) / iqr
                anomalies.append(
                    {
                        "ligne": int(idx),
                        "colonne": col,
                        "score": round(distance, 4),
                        "type": "iqr",
                        "valeur": round(value, 4),
                    }
                )
            elif value > upper_bound:
                distance = (value - upper_bound) / iqr
                anomalies.append(
                    {
                        "ligne": int(idx),
                        "colonne": col,
                        "score": round(distance, 4),
                        "type": "iqr",
                        "valeur": round(value, 4),
                    }
                )

    logger.info(
        "Détection IQR terminée: %d anomalies trouvées (facteur=%.1f)",
        len(anomalies),
        facteur,
    )
    return anomalies
