"""ETL orchestration service.

Manages the full Extract-Transform-Load pipeline: file ingestion,
validation, cleaning, and persistence to the database.
"""

import logging
import os
from pathlib import Path

import pandas as pd

from config.settings import EXPORT_DIR
from models.dataset import Dataset
from repositories.dataset_repository import DatasetRepository
from services.etl.ingestion_service import lire_fichier
from services.etl.validation_service import valider
from services.etl.cleaning_service import nettoyer
from services.audit_service import log_action, log_error

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()


class ValidationError(Exception):
    """Raised when data validation fails during the ETL pipeline."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Validation échouée: {'; '.join(errors)}")


def executer_pipeline(fichier_path: str, user_id: int, nom: str = "") -> Dataset:
    """Execute the full ETL pipeline on a data file.

    Steps:
    1. Ingest the file (read into DataFrame)
    2. Validate the data quality
    3. Clean the data (dedup, fill nulls, normalize columns, convert dates)
    4. Save the Dataset record to the database
    5. Log the audit event

    Args:
        fichier_path: Path to the uploaded file.
        user_id: ID of the user performing the import.
        nom: Optional display name for the dataset.

    Returns:
        The saved Dataset ORM object with all metadata.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is unsupported.
        ValidationError: If the data fails quality checks.
        Exception: For unexpected errors during processing.
    """
    file_path = Path(fichier_path)
    dataset_name = nom or file_path.stem

    logger.info(
        "Démarrage du pipeline ETL pour '%s' (user_id=%d)", dataset_name, user_id
    )

    try:
        # Step 1: Ingestion — read the file
        logger.info("Étape 1/4: Ingestion du fichier...")
        df = lire_fichier(fichier_path)

        # Step 2: Validation — check data quality
        logger.info("Étape 2/4: Validation des données...")
        is_valid, errors = valider(df)
        if not is_valid:
            raise ValidationError(errors)

        # Step 3: Cleaning — preprocess the data
        logger.info("Étape 3/4: Nettoyage des données...")
        df_clean, quality_report = nettoyer(df)

        # Save cleaned file
        clean_dir = Path(EXPORT_DIR) / "datasets"
        clean_dir.mkdir(parents=True, exist_ok=True)
        clean_filename = f"clean_{file_path.stem}.csv"
        clean_path = clean_dir / clean_filename
        df_clean.to_csv(str(clean_path), index=False, encoding="utf-8")

        # Step 4: Persist to database
        logger.info("Étape 4/4: Sauvegarde en base de données...")
        file_size_mo = file_path.stat().st_size / (1024 * 1024)
        extension = file_path.suffix.lower().lstrip(".")

        dataset = Dataset(
            user_id=user_id,
            nom=dataset_name,
            chemin_fichier=str(clean_path),
            format=extension,
            nb_lignes=len(df_clean),
            nb_colonnes=len(df_clean.columns),
            taille_mo=round(file_size_mo, 3),
            colonnes=df_clean.columns.tolist(),
            statut="traite",
        )

        saved_dataset = _dataset_repo.save(dataset)

        # Step 5: Audit log
        log_action(
            user_id=user_id,
            action="import_dataset",
            entite="dataset",
            entite_id=saved_dataset.id,
            statut="succes",
            message=(
                f"Dataset '{dataset_name}' importé avec succès. "
                f"{quality_report['doublons_supprimes']} doublons supprimés, "
                f"{quality_report['valeurs_nulles_remplies']} nulls remplis."
            ),
            ip=None,
        )

        logger.info(
            "Pipeline ETL terminé avec succès: dataset ID=%d, '%s' "
            "(%d lignes, %d colonnes)",
            saved_dataset.id,
            dataset_name,
            len(df_clean),
            len(df_clean.columns),
        )

        # Attach quality report as an attribute for the caller
        saved_dataset._quality_report = quality_report

        return saved_dataset

    except ValidationError:
        log_action(
            user_id=user_id,
            action="import_dataset",
            entite="dataset",
            entite_id=None,
            statut="erreur",
            message=f"Validation échouée pour '{dataset_name}'",
            ip=None,
        )
        raise

    except Exception as e:
        logger.error("Erreur dans le pipeline ETL: %s", e)
        log_error(user_id=user_id, action="import_dataset", error=e, ip=None)
        raise
