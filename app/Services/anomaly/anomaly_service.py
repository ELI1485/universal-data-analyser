"""Anomaly detection orchestration service.

Runs all three anomaly detection algorithms in parallel using
ThreadPoolExecutor and combines the results.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from app.Models.anomaly import Anomaly
from app.Repositories.dataset_repository import DatasetRepository
from app.Repositories.anomaly_repository import AnomalyRepository
from app.Services.anomaly.zscore_detector import detecter as detecter_zscore
from app.Services.anomaly.iqr_detector import detecter as detecter_iqr
from app.Services.anomaly.isolation_detector import detecter as detecter_isolation
from app.Services.audit_service import log_action, log_error
from app.Services.notification_service import NotificationService

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()
_anomaly_repo = AnomalyRepository()


def detecter_toutes(dataset_id: int) -> dict:
    """Run all anomaly detection algorithms on a dataset.

    Executes Z-Score, IQR, and Isolation Forest detectors in parallel
    using a ThreadPoolExecutor. Results are combined and saved to the
    database.

    Args:
        dataset_id: The ID of the dataset to analyze.

    Returns:
        A dictionary with:
        - 'zscore': list of Z-Score anomalies
        - 'iqr': list of IQR anomalies
        - 'isolation': list of Isolation Forest anomalies
        - 'total': total count of all anomalies
        - 'resume': summary by algorithm

    Raises:
        ValueError: If the dataset is not found.
    """
    # Load dataset
    dataset = _dataset_repo.find_by_id(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset avec ID={dataset_id} introuvable.")

    logger.info(
        "Lancement de la détection d'anomalies pour dataset '%s' (ID=%d)",
        dataset.nom,
        dataset_id,
    )

    try:
        # Read the file
        df = pd.read_csv(dataset.chemin_fichier, encoding="utf-8")

        # Run all detectors in parallel
        results = {"zscore": [], "iqr": [], "isolation": []}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(detecter_zscore, df): "zscore",
                executor.submit(detecter_iqr, df): "iqr",
                executor.submit(detecter_isolation, df): "isolation",
            }

            for future in as_completed(futures):
                algo_name = futures[future]
                try:
                    algo_result = future.result()
                    results[algo_name] = algo_result
                    logger.info(
                        "Détecteur '%s' terminé: %d anomalies",
                        algo_name,
                        len(algo_result),
                    )
                except Exception as e:
                    logger.error(
                        "Erreur dans le détecteur '%s': %s", algo_name, e
                    )
                    results[algo_name] = []

        # Convert results to Anomaly ORM objects and save
        anomaly_objects: list[Anomaly] = []

        algo_mapping = {
            "zscore": "zscore",
            "iqr": "iqr",
            "isolation": "isolation_forest",
        }

        for algo_key, anomaly_list in results.items():
            db_algo_name = algo_mapping[algo_key]
            for anomaly_dict in anomaly_list:
                anomaly_obj = Anomaly(
                    dataset_id=dataset_id,
                    algorithme=db_algo_name,
                    score=anomaly_dict["score"],
                    type=anomaly_dict["type"],
                    ligne=anomaly_dict["ligne"],
                    colonne=anomaly_dict["colonne"],
                )
                anomaly_objects.append(anomaly_obj)

        # Save all anomalies to database
        saved_count = 0
        if anomaly_objects:
            saved_count = _anomaly_repo.save_many(anomaly_objects)

        total = sum(len(v) for v in results.values())

        # Log audit
        log_action(
            user_id=dataset.user_id,
            action="detection_anomalies",
            entite="dataset",
            entite_id=dataset_id,
            statut="succes",
            message=(
                f"Détection terminée: {total} anomalies "
                f"(Z-Score: {len(results['zscore'])}, "
                f"IQR: {len(results['iqr'])}, "
                f"Isolation Forest: {len(results['isolation'])})"
            ),
            ip=None,
        )

        result = {
            "zscore": results["zscore"],
            "iqr": results["iqr"],
            "isolation": results["isolation"],
            "total": total,
            "saved_count": saved_count,
            "resume": {
                "zscore_count": len(results["zscore"]),
                "iqr_count": len(results["iqr"]),
                "isolation_count": len(results["isolation"]),
            },
        }

        logger.info(
            "Détection d'anomalies terminée: %d total (%d sauvegardées)",
            total,
            saved_count,
        )

        # Send email notification
        try:
            from app.Repositories.user_repository import UserRepository
            _user_repo = UserRepository()
            user = _user_repo.find_by_id(dataset.user_id)
            if user and user.email:
                notifier = NotificationService()
                all_anom = results["zscore"] + results["iqr"] + results["isolation"]
                all_anom.sort(key=lambda x: x.get("score", 0), reverse=True)
                notifier.envoyer_alerte_anomalies(
                    user_email=user.email,
                    dataset_name=dataset.nom,
                    anomaly_count=total,
                    top_anomalies=all_anom[:5],
                )
        except Exception as notif_err:
            logger.debug("Notification email non envoyée: %s", notif_err)

        return result

    except Exception as e:
        logger.error(
            "Erreur lors de la détection d'anomalies pour dataset ID=%d: %s",
            dataset_id,
            e,
        )
        log_error(
            user_id=dataset.user_id if dataset else None,
            action="detection_anomalies",
            error=e,
            ip=None,
        )
        raise
