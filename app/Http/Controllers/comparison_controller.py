"""Comparison controller for dataset side-by-side analysis."""

import logging

from app.Repositories.dataset_repository import DatasetRepository
from app.Services.comparison_service import comparer_datasets
from app.Services.audit_service import log_action, log_error

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()


class ComparisonController:
    """Controller for dataset comparison operations."""

    def comparer(
        self, id_ancien: int, id_nouveau: int, user_id: int, role: str
    ) -> dict:
        """Compare two datasets with ownership checks.

        Admin can compare any datasets.
        Analyste can only compare their own datasets.

        Args:
            id_ancien: The older dataset's ID.
            id_nouveau: The newer dataset's ID.
            user_id: The requesting user's ID.
            role: The user's role.

        Returns:
            The comparison result dict.

        Raises:
            ValueError: If either dataset not found.
            PermissionError: If user lacks access.
        """
        # Check ownership for non-admin users
        if role != "admin":
            for ds_id in (id_ancien, id_nouveau):
                ds = _dataset_repo.find_by_id(ds_id)
                if not ds:
                    raise ValueError(f"Dataset avec ID={ds_id} introuvable.")
                if ds.user_id != user_id:
                    raise PermissionError(
                        "Accès refusé. Vous ne pouvez comparer que vos propres datasets."
                    )

        try:
            result = comparer_datasets(id_ancien, id_nouveau)

            log_action(
                user_id=user_id,
                action="comparer_datasets",
                entite="dataset",
                entite_id=id_ancien,
                statut="succes",
                message=(
                    f"Comparaison datasets ID={id_ancien} vs ID={id_nouveau}"
                ),
                ip=None,
            )

            logger.info(
                "Comparaison effectuée: ID=%d vs ID=%d par user_id=%d",
                id_ancien, id_nouveau, user_id,
            )
            return result

        except Exception as e:
            logger.error("Erreur comparaison: %s", e)
            log_error(user_id=user_id, action="comparer_datasets", error=e, ip=None)
            raise
