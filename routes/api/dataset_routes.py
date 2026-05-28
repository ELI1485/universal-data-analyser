"""Dataset API routes for upload, listing, and deletion."""

import logging
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.Http.Middleware.dependencies import get_current_user
from app.Http.Controllers.upload_controller import UploadController
from app.Http.Requests.dataset_schema import DatasetResponse, DatasetListResponse

logger = logging.getLogger(__name__)
router = APIRouter()
_upload_ctrl = UploadController()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_dataset(
    file: UploadFile = File(...),
    nom: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a dataset file and run the ETL pipeline.

    Accepts CSV, XLSX, and XLS files. The file is saved to a temp
    directory and then processed through the ETL pipeline.

    Args:
        file: The uploaded file.
        nom: Display name for the dataset.
        current_user: Authenticated user info.

    Returns:
        The created dataset info.
    """
    # Validate file extension
    extension = Path(file.filename).suffix.lower() if file.filename else ""
    if extension not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format non supporté: '{extension}'. Acceptés: .csv, .xlsx, .xls",
        )

    # Save uploaded file temporarily
    upload_dir = Path("./uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / file.filename

    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Run ETL pipeline
        dataset = _upload_ctrl.importer_fichier(
            str(temp_path), nom, current_user["user_id"]
        )

        return {
            "id": dataset.id,
            "nom": dataset.nom,
            "nb_lignes": dataset.nb_lignes,
            "nb_colonnes": dataset.nb_colonnes,
            "taille_mo": dataset.taille_mo,
            "statut": dataset.statut,
            "message": "Dataset importé avec succès.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'importation: {str(e)}",
        )
    finally:
        # Clean up temp file
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.get("/", response_model=DatasetListResponse)
def list_datasets(current_user: dict = Depends(get_current_user)):
    """List all datasets accessible to the current user.

    Admin sees all datasets. Analyste sees only their own.

    Returns:
        A list of datasets with total count.
    """
    datasets = _upload_ctrl.lister_datasets(
        current_user["user_id"], current_user["role"]
    )
    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(ds) for ds in datasets],
        total=len(datasets),
    )


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int, current_user: dict = Depends(get_current_user)
):
    """Delete a dataset by ID.

    Admin can delete any dataset. Analyste can only delete their own.

    Args:
        dataset_id: The dataset's ID.
        current_user: Authenticated user info.
    """
    try:
        _upload_ctrl.supprimer_dataset(
            dataset_id, current_user["user_id"], current_user["role"]
        )
        return {"message": f"Dataset ID={dataset_id} supprimé avec succès."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
