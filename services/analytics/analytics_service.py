"""Analytics orchestration service.

Combines descriptive statistics, trend analysis, KPI computation,
and K-means clustering into a single analysis pipeline.
"""

import logging

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from repositories.dataset_repository import DatasetRepository
from services.analytics.descriptive_statistics import calculer
from services.analytics.trend_analysis import analyser_tendances
from services.analytics.kpi_engine import calculer_kpis
from services.audit_service import log_action, log_error

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()


def analyser(dataset_id: int) -> dict:
    """Run the complete analytics pipeline on a dataset.

    Steps:
    1. Load dataset metadata from the repository
    2. Read the cleaned file with pandas
    3. Run descriptive statistics
    4. Run trend analysis
    5. Compute KPIs
    6. Run K-means clustering (k=3) on numeric columns
    7. Log audit event

    Args:
        dataset_id: The ID of the dataset to analyze.

    Returns:
        A combined results dictionary with keys:
        - 'statistiques': descriptive statistics
        - 'tendances': trend analysis results
        - 'kpis': key performance indicators
        - 'clustering': K-means clustering results
        - 'dataset_info': basic dataset metadata

    Raises:
        ValueError: If the dataset is not found.
        FileNotFoundError: If the dataset file doesn't exist.
    """
    # Step 1: Load dataset from repository
    dataset = _dataset_repo.find_by_id(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset avec ID={dataset_id} introuvable.")

    logger.info("Lancement des analyses pour dataset '%s' (ID=%d)", dataset.nom, dataset_id)

    try:
        # Step 2: Read the file
        df = pd.read_csv(dataset.chemin_fichier, encoding="utf-8")

        # Step 3: Descriptive statistics
        logger.info("Calcul des statistiques descriptives...")
        stats_result = calculer(df)

        # Step 4: Trend analysis
        logger.info("Analyse des tendances...")
        trends_result = analyser_tendances(df)

        # Step 5: KPIs
        logger.info("Calcul des KPIs...")
        kpis_result = calculer_kpis(df)

        # Step 6: K-means clustering
        logger.info("Clustering K-means...")
        clustering_result = _run_clustering(df, n_clusters=3)

        # Step 7: Log audit
        log_action(
            user_id=dataset.user_id,
            action="analyse_complete",
            entite="dataset",
            entite_id=dataset_id,
            statut="succes",
            message=f"Analyse complète effectuée sur '{dataset.nom}'",
            ip=None,
        )

        result = {
            "dataset_info": {
                "id": dataset.id,
                "nom": dataset.nom,
                "nb_lignes": dataset.nb_lignes,
                "nb_colonnes": dataset.nb_colonnes,
                "format": dataset.format,
            },
            "statistiques": stats_result,
            "tendances": trends_result,
            "kpis": kpis_result,
            "clustering": clustering_result,
        }

        logger.info("Analyses terminées avec succès pour dataset ID=%d", dataset_id)
        return result

    except Exception as e:
        logger.error("Erreur lors de l'analyse du dataset ID=%d: %s", dataset_id, e)
        log_error(
            user_id=dataset.user_id if dataset else None,
            action="analyse_complete",
            error=e,
            ip=None,
        )
        raise


def _run_clustering(df: pd.DataFrame, n_clusters: int = 3) -> dict:
    """Run K-means clustering on numeric columns.

    Args:
        df: The DataFrame to cluster.
        n_clusters: Number of clusters (default: 3).

    Returns:
        A dictionary with clustering results:
        - 'n_clusters': number of clusters used
        - 'cluster_sizes': count per cluster
        - 'cluster_centers': centroid values per cluster
        - 'inertia': sum of squared distances to centroids
        - 'labels': cluster assignment for first 100 rows
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(numeric_cols) < 2:
        return {
            "n_clusters": 0,
            "message": "Moins de 2 colonnes numériques, clustering non applicable.",
            "cluster_sizes": {},
            "cluster_centers": {},
            "inertia": 0.0,
        }

    # Prepare data: use numeric columns, drop rows with NaN
    df_numeric = df[numeric_cols].dropna()

    if len(df_numeric) < n_clusters:
        return {
            "n_clusters": 0,
            "message": f"Pas assez de lignes ({len(df_numeric)}) pour {n_clusters} clusters.",
            "cluster_sizes": {},
            "cluster_centers": {},
            "inertia": 0.0,
        }

    try:
        # Standardize features
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_numeric)

        # Run K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(df_scaled)

        # Cluster sizes
        unique, counts = np.unique(labels, return_counts=True)
        cluster_sizes = {int(k): int(v) for k, v in zip(unique, counts)}

        # Cluster centers (in original scale)
        centers_original = scaler.inverse_transform(kmeans.cluster_centers_)
        cluster_centers = {}
        for i, center in enumerate(centers_original):
            cluster_centers[f"cluster_{i}"] = {
                col: round(float(val), 4)
                for col, val in zip(numeric_cols, center)
            }

        result = {
            "n_clusters": n_clusters,
            "cluster_sizes": cluster_sizes,
            "cluster_centers": cluster_centers,
            "inertia": round(float(kmeans.inertia_), 4),
            "colonnes_utilisees": numeric_cols,
            "nb_lignes_analysees": len(df_numeric),
            "labels_sample": [int(l) for l in labels[:100]],
        }

        logger.info(
            "Clustering terminé: %d clusters, tailles=%s",
            n_clusters,
            cluster_sizes,
        )
        return result

    except Exception as e:
        logger.warning("Erreur lors du clustering: %s", e)
        return {
            "n_clusters": 0,
            "message": f"Erreur clustering: {str(e)}",
            "cluster_sizes": {},
            "cluster_centers": {},
            "inertia": 0.0,
        }
