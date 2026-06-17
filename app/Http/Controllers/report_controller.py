"""Report controller for generating and managing reports."""

import logging

from app.Models.report import Report
from app.Repositories.dataset_repository import DatasetRepository
from app.Repositories.report_repository import ReportRepository
from app.Services.reporting.report_service import generer_rapport
from app.Services.audit_service import log_action, log_error

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()
_report_repo = ReportRepository()


class ReportController:
    """Controller for report generation and retrieval operations."""

    def generer(
        self,
        dataset_id: int,
        user_id: int,
        format: str,
        selected_charts: list[str] | None = None,
        max_charts: int | None = None,
    ) -> Report:
        """Generate a report for a dataset.

        Args:
            dataset_id: The dataset to report on.
            user_id: The requesting user's ID.
            format: Report format ('pdf' or 'excel').
            selected_charts: Chart labels chosen by the user. When None, all
                available charts are included (backward-compatible default).
            max_charts: Maximum number of diagrams to include. When None, no limit.

        Returns:
            The saved Report object.

        Raises:
            ValueError: If dataset not found or format invalid.
        """
        try:
            logger.info(
                "Génération rapport %s pour dataset_id=%d, user_id=%d",
                format,
                dataset_id,
                user_id,
            )
            report = generer_rapport(
                dataset_id, user_id, format, selected_charts, max_charts
            )
            return report
        except Exception as e:
            logger.error("Erreur génération rapport: %s", e)
            log_error(user_id=user_id, action="generer_rapport", error=e, ip=None)
            raise

    def lister_rapports(self, user_id: int, role: str) -> list[Report]:
        """List reports accessible to the user.

        Admin sees all reports. Analyste sees only their own.

        Args:
            user_id: The requesting user's ID.
            role: The user's role.

        Returns:
            A list of Report objects.
        """
        if role == "admin":
            reports = _report_repo.find_all()
        else:
            reports = _report_repo.find_by_user(user_id)

        logger.info(
            "Liste rapports: %d résultats pour user_id=%d", len(reports), user_id
        )
        return reports

    def telecharger(self, report_id: int, user_id: int, role: str) -> str:
        """Get the file path of a report for download.

        Checks ownership for Analyste role.

        Args:
            report_id: The report's ID.
            user_id: The requesting user's ID.
            role: The user's role.

        Returns:
            The file path to the report.

        Raises:
            ValueError: If report not found.
            PermissionError: If user lacks access.
        """
        report = _report_repo.find_by_id(report_id)
        if not report:
            raise ValueError(f"Rapport avec ID={report_id} introuvable.")

        if role != "admin" and report.user_id != user_id:
            raise PermissionError(
                "Accès refusé. Vous ne pouvez télécharger que vos propres rapports."
            )

        log_action(
            user_id=user_id,
            action="telecharger_rapport",
            entite="report",
            entite_id=report_id,
            statut="succes",
            message=f"Téléchargement rapport ID={report_id}",
            ip=None,
        )

        return report.chemin_export
