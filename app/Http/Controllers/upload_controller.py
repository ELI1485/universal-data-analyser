"""Upload controller for dataset import and management."""

import logging
from typing import Optional

from app.Models.dataset import Dataset
from app.Services.etl.etl_service import executer_pipeline
from app.Services.audit_service import log_action, log_error
from app.Repositories.dataset_repository import DatasetRepository

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()


class UploadController:
    """Controller for file upload and dataset management operations."""

    def importer_fichier(self, fichier_path: str, nom: str, user_id: int) -> Dataset:
        """Import a file and execute the ETL pipeline.

        Args:
            fichier_path: Path to the uploaded file.
            nom: Display name for the dataset.
            user_id: ID of the uploading user.

        Returns:
            The saved Dataset object.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If format is unsupported or validation fails.
            Exception: For other pipeline errors.
        """
        try:
            logger.info(
                "Importation fichier '%s' par user_id=%d", nom, user_id
            )
            dataset = executer_pipeline(fichier_path, user_id, nom)
            return dataset
        except Exception as e:
            logger.error("Erreur importation fichier: %s", e)
            log_error(user_id=user_id, action="importer_fichier", error=e, ip=None)
            raise

    def lister_datasets(self, user_id: int, role: str) -> list[Dataset]:
        """List datasets accessible to the user.

        Admin can see all datasets. Analyste can only see their own.

        Args:
            user_id: The requesting user's ID.
            role: The user's role ('admin' or 'analyste').

        Returns:
            A list of Dataset objects.
        """
        if role == "admin":
            datasets = _dataset_repo.find_all()
        else:
            datasets = _dataset_repo.find_by_user(user_id)

        logger.info(
            "Liste datasets: %d résultats pour user_id=%d (role=%s)",
            len(datasets),
            user_id,
            role,
        )
        return datasets

    def supprimer_dataset(self, dataset_id: int, user_id: int, role: str) -> bool:
        """Delete a dataset.

        Admin can delete any dataset. Analyste can only delete their own.

        Args:
            dataset_id: The ID of the dataset to delete.
            user_id: The requesting user's ID.
            role: The user's role.

        Returns:
            True if deleted successfully.

        Raises:
            PermissionError: If the user lacks permission.
            ValueError: If the dataset is not found.
        """
        dataset = _dataset_repo.find_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset avec ID={dataset_id} introuvable.")

        # Check ownership for non-admin
        if role != "admin" and dataset.user_id != user_id:
            raise PermissionError(
                "Accès refusé. Vous ne pouvez supprimer que vos propres datasets."
            )

        result = _dataset_repo.delete(dataset_id)

        log_action(
            user_id=user_id,
            action="supprimer_dataset",
            entite="dataset",
            entite_id=dataset_id,
            statut="succes",
            message=f"Dataset '{dataset.nom}' supprimé",
            ip=None,
        )

        logger.info("Dataset ID=%d supprimé par user_id=%d", dataset_id, user_id)
        return result
