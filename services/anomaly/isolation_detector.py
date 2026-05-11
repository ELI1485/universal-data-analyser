"""Isolation Forest anomaly detection.

Uses scikit-learn's IsolationForest to detect multivariate anomalies
across all numeric columns simultaneously.
"""

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def detecter(df: pd.DataFrame, contamination: float = 0.05) -> list[dict]:
    """Detect anomalies using the Isolation Forest algorithm.

    Uses scikit-learn's IsolationForest on all numeric columns to
    identify multivariate anomalies.

    Args:
        df: The pandas DataFrame to analyze.
        contamination: Expected proportion of outliers (default: 0.05 = 5%).

    Returns:
        A list of anomaly dictionaries, each containing:
        - 'ligne': row index
        - 'colonne': 'multi' (since it's multivariate detection)
        - 'score': anomaly score (negative = more anomalous)
        - 'type': 'isolation_forest'
        - 'valeur': the anomaly score from the model
    """
    anomalies: list[dict] = []
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(numeric_cols) < 1:
        logger.info("Aucune colonne numérique pour Isolation Forest.")
        return anomalies

    # Prepare data
    df_numeric = df[numeric_cols].dropna()

    if len(df_numeric) < 10:
        logger.warning(
            "Pas assez de données pour Isolation Forest (%d lignes).", len(df_numeric)
        )
        return anomalies

    try:
        # Standardize features
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(df_numeric)

        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            n_jobs=-1,
        )
        predictions = iso_forest.fit_predict(data_scaled)
        scores = iso_forest.decision_function(data_scaled)

        # Find anomalies (predictions == -1)
        anomaly_indices = df_numeric.index[predictions == -1]

        for idx in anomaly_indices:
            # Find which position in the array corresponds to this index
            position = df_numeric.index.get_loc(idx)
            anomaly_score = float(scores[position])

            # Find the most anomalous column for this row
            row_data = data_scaled[position]
            most_anomalous_col_idx = int(np.argmax(np.abs(row_data)))
            most_anomalous_col = numeric_cols[most_anomalous_col_idx]

            anomalies.append(
                {
                    "ligne": int(idx),
                    "colonne": most_anomalous_col,
                    "score": round(abs(anomaly_score), 4),
                    "type": "isolation_forest",
                    "valeur": round(float(df_numeric.loc[idx, most_anomalous_col]), 4),
                }
            )

        logger.info(
            "Détection Isolation Forest terminée: %d anomalies trouvées "
            "(contamination=%.2f)",
            len(anomalies),
            contamination,
        )

    except Exception as e:
        logger.error("Erreur lors de la détection Isolation Forest: %s", e)

    return anomalies
