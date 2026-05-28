"""Z-Score anomaly detection.

Detects anomalies by computing the Z-Score for each numeric column
and flagging values where |z| exceeds the threshold.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def detecter(df: pd.DataFrame, seuil: float = 3.0) -> list[dict]:
    """Detect anomalies using the Z-Score method.

    For each numeric column, computes the Z-Score and flags rows
    where the absolute Z-Score exceeds the threshold.

    Args:
        df: The pandas DataFrame to analyze.
        seuil: The Z-Score threshold (default: 3.0). Values with |z| > seuil
               are flagged as anomalies.

    Returns:
        A list of anomaly dictionaries, each containing:
        - 'ligne': row index
        - 'colonne': column name
        - 'score': absolute Z-Score value
        - 'type': 'zscore'
        - 'valeur': the actual value that is anomalous
    """
    anomalies: list[dict] = []
    numeric_cols = df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        col_data = df[col].dropna()

        if len(col_data) < 3:
            continue

        # Compute Z-scores
        mean_val = col_data.mean()
        std_val = col_data.std()

        if std_val == 0 or np.isnan(std_val):
            continue

        z_scores = np.abs((col_data - mean_val) / std_val)

        # Find anomalies
        anomaly_mask = z_scores > seuil
        anomaly_indices = col_data[anomaly_mask].index

        for idx in anomaly_indices:
            score = float(z_scores.loc[idx])
            valeur = float(df[col].iloc[idx]) if idx < len(df) else float(col_data.loc[idx])

            anomalies.append(
                {
                    "ligne": int(idx),
                    "colonne": col,
                    "score": round(score, 4),
                    "type": "zscore",
                    "valeur": round(valeur, 4),
                }
            )

    logger.info(
        "Détection Z-Score terminée: %d anomalies trouvées (seuil=%.1f)",
        len(anomalies),
        seuil,
    )
    return anomalies
