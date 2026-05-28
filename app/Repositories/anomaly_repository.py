"""Anomaly repository for database operations on the anomalies table."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func

from database.connection import get_db
from app.Models.anomaly import Anomaly

logger = logging.getLogger(__name__)


class AnomalyRepository:
    """Repository handling all CRUD operations for Anomaly entities."""

    def save_many(self, anomalies: list[Anomaly]) -> int:
        """Save multiple anomalies to the database in bulk.

        Args:
            anomalies: A list of Anomaly objects to persist.

        Returns:
            The number of anomalies saved.
        """
        if not anomalies:
            return 0

        with get_db() as db:
            db.add_all(anomalies)
            db.flush()
            count = len(anomalies)
            logger.info("Anomalies sauvegardées en masse: %d entrées", count)
            return count

    def find_by_dataset(self, dataset_id: int) -> list[Anomaly]:
        """Find all anomalies for a specific dataset.

        Args:
            dataset_id: The dataset's ID.

        Returns:
            A list of Anomaly objects.
        """
        with get_db() as db:
            anomalies = (
                db.query(Anomaly)
                .filter(Anomaly.dataset_id == dataset_id)
                .order_by(Anomaly.score.desc())
                .all()
            )
            for a in anomalies:
                db.expunge(a)
            return anomalies

    def find_by_algorithm(self, dataset_id: int, algorithme: str) -> list[Anomaly]:
        """Find anomalies for a dataset filtered by detection algorithm.

        Args:
            dataset_id: The dataset's ID.
            algorithme: The algorithm name ('zscore', 'iqr', 'isolation_forest').

        Returns:
            A list of Anomaly objects matching the filter.
        """
        with get_db() as db:
            anomalies = (
                db.query(Anomaly)
                .filter(
                    Anomaly.dataset_id == dataset_id,
                    Anomaly.algorithme == algorithme,
                )
                .order_by(Anomaly.score.desc())
                .all()
            )
            for a in anomalies:
                db.expunge(a)
            return anomalies

    def count_by_type(self, dataset_id: int) -> dict:
        """Count anomalies grouped by algorithm type for a dataset.

        Args:
            dataset_id: The dataset's ID.

        Returns:
            A dict mapping algorithm names to their anomaly count.
        """
        with get_db() as db:
            results = (
                db.query(Anomaly.algorithme, func.count(Anomaly.id))
                .filter(Anomaly.dataset_id == dataset_id)
                .group_by(Anomaly.algorithme)
                .all()
            )
            return {algo: count for algo, count in results}

    def count_recent(self, days: int = 30) -> int:
        """Count anomalies detected in the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            Total count of recently detected anomalies.
        """
        with get_db() as db:
            cutoff = datetime.utcnow() - timedelta(days=days)
            count = (
                db.query(func.count(Anomaly.id))
                .filter(Anomaly.detectee_le >= cutoff)
                .scalar()
            )
            return count or 0
