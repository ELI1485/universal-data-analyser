"""Report API routes for generating and downloading reports."""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.Http.Middleware.dependencies import get_current_user
from app.Http.Controllers.report_controller import ReportController
from app.Http.Requests.report_schema import ReportRequest

logger = logging.getLogger(__name__)
router = APIRouter()
_report_ctrl = ReportController()


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_report(
    request: ReportRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a PDF or Excel report for a dataset.

    Runs full analytics, anomaly detection, and LLM insights,
    then compiles them into the requested format.

    Args:
        request: Report generation request (dataset_id + format).
        current_user: Authenticated user info.

    Returns:
        Report metadata.
    """
    try:
        report = _report_ctrl.generer(
            request.dataset_id,
            current_user["user_id"],
            request.format.value,
        )
        return {
            "id": report.id,
            "dataset_id": report.dataset_id,
            "format": report.format,
            "chemin_export": report.chemin_export,
            "taille_ko": report.taille_ko,
            "message": f"Rapport {report.format.upper()} généré avec succès.",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}",
        )


@router.get("/")
def list_reports(current_user: dict = Depends(get_current_user)):
    """List all reports accessible to the current user.

    Returns:
        A list of report metadata.
    """
    reports = _report_ctrl.lister_rapports(
        current_user["user_id"], current_user["role"]
    )
    return {
        "reports": [
            {
                "id": r.id,
                "dataset_id": r.dataset_id,
                "format": r.format,
                "taille_ko": r.taille_ko,
                "genere_le": str(r.genere_le) if r.genere_le else None,
            }
            for r in reports
        ],
        "total": len(reports),
    }


@router.get("/{report_id}/download")
def download_report(
    report_id: int, current_user: dict = Depends(get_current_user)
):
    """Download a generated report file.

    Args:
        report_id: The report's ID.
        current_user: Authenticated user info.

    Returns:
        The report file as a download.
    """
    try:
        file_path = _report_ctrl.telecharger(
            report_id, current_user["user_id"], current_user["role"]
        )

        path = Path(file_path)
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Le fichier du rapport n'existe plus sur le serveur.",
            )

        media_type = (
            "application/pdf"
            if path.suffix == ".pdf"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        return FileResponse(
            path=str(path),
            filename=path.name,
            media_type=media_type,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
