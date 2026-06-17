"""Report service orchestrating report generation.

Combines analytics, anomaly detection, and LLM insights into
a PDF or Excel report, then persists the report metadata.
"""

import logging
import os
from pathlib import Path

from app.Models.report import Report
from app.Repositories.dataset_repository import DatasetRepository
from app.Repositories.report_repository import ReportRepository
from app.Services.analytics.analytics_service import analyser
from app.Services.anomaly.anomaly_service import detecter_toutes
from app.Services.llm_service import LLMService
from app.Services.reporting.pdf_generator import generer as generer_pdf
from app.Services.reporting.excel_generator import generer as generer_excel
from app.Services.audit_service import log_action, log_error
from app.Services.notification_service import NotificationService

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()
_report_repo = ReportRepository()


def generer_rapport(
    dataset_id: int,
    user_id: int,
    format: str,
    selected_charts: list[str] | None = None,
    max_charts: int | None = None,
) -> Report:
    """Generate a complete report for a dataset.

    Steps:
    1. Get analytics results
    2. Get anomaly detection results
    3. Generate LLM insights
    4. Call PDF or Excel generator based on format
    5. Save Report record to database
    6. Log audit event

    Args:
        dataset_id: The dataset ID to report on.
        user_id: The user requesting the report.
        format: Report format ('pdf' or 'excel').
        selected_charts: Chart labels chosen by the user. When None, all
            available charts are included (backward-compatible default).
        max_charts: Maximum number of diagrams to include. When None, no limit.

    Returns:
        The saved Report ORM object.

    Raises:
        ValueError: If dataset not found or format is invalid.
    """
    if format not in ("pdf", "excel"):
        raise ValueError(f"Format de rapport invalide: '{format}'. Utilisez 'pdf' ou 'excel'.")

    dataset = _dataset_repo.find_by_id(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset avec ID={dataset_id} introuvable.")

    logger.info(
        "Génération rapport %s pour dataset '%s' (ID=%d)",
        format.upper(),
        dataset.nom,
        dataset_id,
    )

    try:
        # Step 1: Get analytics results
        analytics = analyser(dataset_id)

        # Step 2: Get anomalies
        anomalies = detecter_toutes(dataset_id)

        # Step 3: Generate LLM insights
        insights = _generate_insights(dataset, analytics, anomalies)

        # Step 4: Generate report file
        if format == "pdf":
            file_path = generer_pdf(
                dataset_id, user_id, analytics, anomalies, insights,
                selected_charts, max_charts,
            )
        else:
            file_path = generer_excel(
                dataset_id, user_id, analytics, anomalies, insights,
                selected_charts, max_charts,
            )

        # Step 5: Save report to database
        file_size_ko = os.path.getsize(file_path) / 1024
        report = Report(
            dataset_id=dataset_id,
            user_id=user_id,
            format=format,
            chemin_export=file_path,
            taille_ko=round(file_size_ko, 2),
        )
        saved_report = _report_repo.save(report)

        # Step 6: Log audit
        log_action(
            user_id=user_id,
            action="generer_rapport",
            entite="report",
            entite_id=saved_report.id,
            statut="succes",
            message=f"Rapport {format.upper()} généré pour dataset '{dataset.nom}'",
            ip=None,
        )

        logger.info(
            "Rapport généré avec succès: ID=%d, format=%s, taille=%.1f Ko",
            saved_report.id,
            format,
            file_size_ko,
        )

        # Send email notification
        try:
            from app.Repositories.user_repository import UserRepository
            _user_repo = UserRepository()
            user = _user_repo.find_by_id(user_id)
            if user and user.email:
                notifier = NotificationService()
                notifier.envoyer_rapport_pret(
                    user_email=user.email,
                    report_format=format,
                    dataset_name=dataset.nom,
                )
        except Exception as notif_err:
            logger.debug("Notification email non envoyée: %s", notif_err)

        return saved_report

    except Exception as e:
        logger.error("Erreur lors de la génération du rapport: %s", e)
        log_error(user_id=user_id, action="generer_rapport", error=e, ip=None)
        raise


def _generate_insights(dataset, analytics: dict, anomalies: dict) -> str:
    """Generate LLM insights from analytics and anomaly data.

    Args:
        dataset: The Dataset ORM object.
        analytics: The analytics results dictionary.
        anomalies: The anomaly detection results.

    Returns:
        The LLM-generated insights text. When the LLM service is
        unavailable, the returned string includes the real underlying
        reason (missing API key, missing module, etc.) so the bug can be
        diagnosed from the report itself.
    """
    try:
        llm = LLMService()

        # Build context for LLM
        stats_summary = ""
        stats_data = analytics.get("statistiques", {}).get("colonnes", {})
        for col_name, col_stats in list(stats_data.items())[:5]:
            kind = col_stats.get("_kind", "numeric")
            if kind == "categorical":
                stats_summary += (
                    f"  {col_name} (categoriel): "
                    f"{col_stats.get('unique_count')} valeurs uniques, "
                    f"mode='{col_stats.get('mode')}' "
                    f"({col_stats.get('mode_frequency_pct')}%)\n"
                )
            else:
                stats_summary += (
                    f"  {col_name}: moy={col_stats.get('mean')}, "
                    f"med={col_stats.get('median')}, "
                    f"ecart-type={col_stats.get('std')}\n"
                )

        # Top anomalies
        all_anom = (
            anomalies.get("zscore", [])
            + anomalies.get("iqr", [])
            + anomalies.get("isolation", [])
        )
        all_anom.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_anomalies = all_anom[:5]

        # Correlations
        kpis = analytics.get("kpis", {})
        correlations = kpis.get("top_correlated_pairs", [])

        context = {
            "dataset_name": dataset.nom,
            "nb_rows": dataset.nb_lignes,
            "nb_cols": dataset.nb_colonnes,
            "stats_summary": stats_summary,
            "anomalies_count": anomalies.get("total", 0),
            "top_anomalies": top_anomalies,
            "correlations": correlations,
        }

        # generer_insights() now embeds the real reason on failure, so we
        # no longer need to mask it behind a generic fallback message.
        return llm.generer_insights(context)

    except Exception as e:
        logger.warning("Generation d'insights LLM echouee: %s", e)
        return (
            "L'analyse par intelligence artificielle n'est pas disponible. "
            f"Detail: {type(e).__name__}: {e}"
        )
