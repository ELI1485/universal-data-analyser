"""Analytics controller for running and retrieving analysis results."""

import logging

from repositories.dataset_repository import DatasetRepository
from repositories.anomaly_repository import AnomalyRepository
from services.analytics.analytics_service import analyser
from services.anomaly.anomaly_service import detecter_toutes
from services.audit_service import log_action, log_error

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()
_anomaly_repo = AnomalyRepository()


class AnalyticsController:
    """Controller for analytics and anomaly detection operations."""

    def executer_analyses(self, dataset_id: int, user_id: int) -> dict:
        """Execute full analytics and anomaly detection on a dataset.

        Args:
            dataset_id: The dataset to analyze.
            user_id: The requesting user's ID.

        Returns:
            A dict with 'analytics' and 'anomalies' results.

        Raises:
            ValueError: If the dataset is not found.
            PermissionError: If user lacks access.
        """
        try:
            logger.info(
                "Exécution analyses pour dataset_id=%d, user_id=%d",
                dataset_id,
                user_id,
            )

            # Run analytics
            analytics_result = analyser(dataset_id)

            # Run anomaly detection
            anomalies_result = detecter_toutes(dataset_id)

            result = {
                "analytics": analytics_result,
                "anomalies": anomalies_result,
            }

            logger.info("Analyses terminées pour dataset_id=%d", dataset_id)
            return result

        except Exception as e:
            logger.error("Erreur analyses dataset_id=%d: %s", dataset_id, e)
            log_error(user_id=user_id, action="executer_analyses", error=e, ip=None)
            raise

    def obtenir_resultats(self, dataset_id: int, user_id: int, role: str) -> dict:
        """Retrieve existing analysis results for a dataset.

        Checks ownership for Analyste role.

        Args:
            dataset_id: The dataset ID.
            user_id: The requesting user's ID.
            role: The user's role.

        Returns:
            A dict with analytics and anomalies data.

        Raises:
            ValueError: If dataset not found.
            PermissionError: If user lacks access.
        """
        # Check dataset exists and ownership
        dataset = _dataset_repo.find_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset avec ID={dataset_id} introuvable.")

        if role != "admin" and dataset.user_id != user_id:
            raise PermissionError(
                "Accès refusé. Vous ne pouvez voir que vos propres analyses."
            )

        # Get stored anomalies
        anomalies = _anomaly_repo.find_by_dataset(dataset_id)
        anomaly_counts = _anomaly_repo.count_by_type(dataset_id)

        # Format anomalies
        anomalies_list = [
            {
                "id": a.id,
                "algorithme": a.algorithme,
                "score": a.score,
                "type": a.type,
                "ligne": a.ligne,
                "colonne": a.colonne,
                "detectee_le": str(a.detectee_le) if a.detectee_le else None,
            }
            for a in anomalies
        ]

        result = {
            "dataset_info": {
                "id": dataset.id,
                "nom": dataset.nom,
                "nb_lignes": dataset.nb_lignes,
                "nb_colonnes": dataset.nb_colonnes,
                "statut": dataset.statut,
            },
            "anomalies": anomalies_list,
            "anomaly_counts": anomaly_counts,
            "total_anomalies": len(anomalies),
        }

        logger.info(
            "Résultats récupérés pour dataset_id=%d: %d anomalies",
            dataset_id,
            len(anomalies),
        )
        return result
