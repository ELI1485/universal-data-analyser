"""Dataset repository for database operations on the datasets table."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from database.connection import get_db
from models.dataset import Dataset

logger = logging.getLogger(__name__)


class DatasetRepository:
    """Repository handling all CRUD operations for Dataset entities."""

    def save(self, dataset: Dataset) -> Dataset:
        """Save a new dataset to the database.

        Args:
            dataset: The Dataset object to persist.

        Returns:
            The persisted Dataset object with generated ID.
        """
        with get_db() as db:
            db.add(dataset)
            db.flush()
            db.expunge(dataset)
            logger.info("Dataset sauvegardé: ID=%d, nom='%s'", dataset.id, dataset.nom)
            return dataset

    def find_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Find a dataset by its primary key.

        Args:
            dataset_id: The dataset's ID.

        Returns:
            The Dataset object or None if not found.
        """
        with get_db() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                db.expunge(dataset)
            return dataset

    def find_by_user(self, user_id: int) -> list[Dataset]:
        """Find all datasets belonging to a specific user.

        Args:
            user_id: The owner user's ID.

        Returns:
            A list of Dataset objects belonging to the user.
        """
        with get_db() as db:
            datasets = (
                db.query(Dataset)
                .filter(Dataset.user_id == user_id)
                .order_by(Dataset.cree_le.desc())
                .all()
            )
            for ds in datasets:
                db.expunge(ds)
            return datasets

    def find_all(self) -> list[Dataset]:
        """Retrieve all datasets from the database.

        Returns:
            A list of all Dataset objects.
        """
        with get_db() as db:
            datasets = db.query(Dataset).order_by(Dataset.cree_le.desc()).all()
            for ds in datasets:
                db.expunge(ds)
            return datasets

    def update_status(self, dataset_id: int, statut: str) -> None:
        """Update the processing status of a dataset.

        Args:
            dataset_id: The dataset's ID.
            statut: The new status value.
        """
        with get_db() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.statut = statut
                logger.info(
                    "Statut dataset ID=%d mis à jour: '%s'", dataset_id, statut
                )

    def delete(self, dataset_id: int) -> bool:
        """Delete a dataset from the database.

        Args:
            dataset_id: The dataset's ID.

        Returns:
            True if deleted, False if not found.
        """
        with get_db() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                logger.warning("Dataset non trouvé pour suppression: ID=%d", dataset_id)
                return False
            db.delete(dataset)
            logger.info("Dataset supprimé: ID=%d", dataset_id)
            return True
