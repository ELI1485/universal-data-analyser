"""Ingestion service for reading data files into DataFrames.

Supports CSV (with encoding detection), XLSX, and XLS file formats.
Enforces file size limits from application settings.
"""

import logging
import os
from pathlib import Path

import pandas as pd

from config.settings import MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)


def lire_fichier(chemin: str) -> pd.DataFrame:
    """Read a data file and return it as a pandas DataFrame.

    Supports .csv, .xlsx, and .xls formats. For CSV files, attempts
    UTF-8 encoding first, then falls back to Latin-1.

    Args:
        chemin: Path to the file to read.

    Returns:
        A pandas DataFrame containing the file data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or the file exceeds size limit.
        pd.errors.EmptyDataError: If the file is empty.
        Exception: For other read errors (malformed files, etc.).
    """
    file_path = Path(chemin)

    # Check file exists
    if not file_path.exists():
        logger.error("Fichier introuvable: %s", chemin)
        raise FileNotFoundError(f"Le fichier n'existe pas: {chemin}")

    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        logger.error(
            "Fichier trop volumineux: %.2f Mo (max: %d Mo)",
            file_size_mb,
            MAX_FILE_SIZE_MB,
        )
        raise ValueError(
            f"Le fichier est trop volumineux ({file_size_mb:.2f} Mo). "
            f"Taille maximale autorisée: {MAX_FILE_SIZE_MB} Mo."
        )

    # Determine file extension
    extension = file_path.suffix.lower()

    if extension == ".csv":
        df = _lire_csv(chemin)
    elif extension == ".xlsx":
        df = _lire_excel(chemin, engine="openpyxl")
    elif extension == ".xls":
        df = _lire_excel(chemin, engine="xlrd")
    else:
        logger.error("Format de fichier non supporté: %s", extension)
        raise ValueError(
            f"Format de fichier non supporté: '{extension}'. "
            f"Formats acceptés: .csv, .xlsx, .xls"
        )

    if df.empty:
        logger.warning("Le fichier est vide ou ne contient pas de données: %s", chemin)
        raise pd.errors.EmptyDataError(
            f"Le fichier ne contient pas de données: {chemin}"
        )

    logger.info(
        "Fichier lu avec succès: %s (%d lignes, %d colonnes)",
        chemin,
        len(df),
        len(df.columns),
    )
    return df


def _lire_csv(chemin: str) -> pd.DataFrame:
    """Read a CSV file with encoding detection.

    Tries UTF-8 first, then falls back to Latin-1 (ISO-8859-1).

    Args:
        chemin: Path to the CSV file.

    Returns:
        A pandas DataFrame.

    Raises:
        Exception: If the file cannot be read with any supported encoding.
    """
    # Try UTF-8 first
    try:
        df = pd.read_csv(chemin, encoding="utf-8", on_bad_lines="warn")
        logger.debug("CSV lu en UTF-8: %s", chemin)
        return df
    except UnicodeDecodeError:
        logger.debug("UTF-8 échoué pour %s, tentative en Latin-1...", chemin)

    # Fallback to Latin-1
    try:
        df = pd.read_csv(chemin, encoding="latin-1", on_bad_lines="warn")
        logger.debug("CSV lu en Latin-1: %s", chemin)
        return df
    except Exception as e:
        logger.error("Impossible de lire le fichier CSV %s: %s", chemin, e)
        raise ValueError(
            f"Impossible de lire le fichier CSV. "
            f"Vérifiez que le fichier est un CSV valide. Erreur: {e}"
        )


def _lire_excel(chemin: str, engine: str) -> pd.DataFrame:
    """Read an Excel file.

    Args:
        chemin: Path to the Excel file.
        engine: The pandas engine to use ('openpyxl' or 'xlrd').

    Returns:
        A pandas DataFrame.

    Raises:
        Exception: If the file cannot be read.
    """
    try:
        # sheet_name=None reads all sheets into a dictionary: {sheet_name: DataFrame}
        sheets_dict = pd.read_excel(chemin, engine=engine, sheet_name=None)
        
        combined_dfs = []
        for sheet_name, sheet_df in sheets_dict.items():
            if not sheet_df.empty:
                # Optional: keep track of which sheet the data came from
                sheet_df["Source_Feuille"] = sheet_name
                combined_dfs.append(sheet_df)
                
        if not combined_dfs:
            # All sheets were empty
            df = pd.DataFrame()
        else:
            # Concatenate all sheets into a single DataFrame
            df = pd.concat(combined_dfs, ignore_index=True)
            
        logger.debug("Excel lu avec moteur '%s' (%d feuilles combinées): %s", engine, len(combined_dfs), chemin)
        return df
    except Exception as e:
        logger.error("Impossible de lire le fichier Excel %s: %s", chemin, e)
        raise ValueError(
            f"Impossible de lire le fichier Excel. "
            f"Vérifiez que le fichier est valide. Erreur: {e}"
        )
