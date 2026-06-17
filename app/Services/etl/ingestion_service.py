"""Ingestion service for reading data files into DataFrames.

Supports CSV (with encoding detection), XLSX, and XLS file formats.
Enforces file size limits from application settings.
"""

import logging
import os
import re
import unicodedata
from pathlib import Path

import pandas as pd

from config.settings import MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

# Name of the column used to track which Excel sheet a row originated from.
SOURCE_SHEET_COLUMN = "Source_Feuille"


def _normaliser_nom_colonne(nom: object) -> str:
    """Normalize a column name so equivalent headers across sheets align.

    Strips whitespace, lowercases, removes accents (é → e), and collapses
    separators to single underscores. This makes "Filière", "filiere" and
    "Filiere" map to the same canonical name so multi-sheet concatenation
    keeps them in a single column instead of creating misaligned NaNs.

    Args:
        nom: The raw column header.

    Returns:
        A canonical column name.
    """
    texte = str(nom).strip().lower()
    # Drop accents: "filière" -> "filiere"
    texte = (
        unicodedata.normalize("NFKD", texte)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    texte = re.sub(r"[\s\-.]+", "_", texte)
    texte = re.sub(r"[^a-z0-9_]", "", texte)
    texte = re.sub(r"_+", "_", texte).strip("_")
    return texte or "colonne"


def _normaliser_colonnes_feuille(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with canonical, de-duplicated column names."""
    nouveaux: list[str] = []
    vus: dict[str, int] = {}
    for col in df.columns:
        base = _normaliser_nom_colonne(col)
        if base in vus:
            vus[base] += 1
            nouveaux.append(f"{base}_{vus[base]}")
        else:
            vus[base] = 0
            nouveaux.append(base)
    df = df.copy()
    df.columns = nouveaux
    return df


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

        # 1. Normalize each sheet's column names BEFORE concatenation so that
        #    equivalent headers (e.g. "Filière" / "filiere" / "Filiere") align
        #    into a single column instead of producing misaligned NaN columns.
        feuilles: list[tuple[str, pd.DataFrame]] = []
        for sheet_name, sheet_df in sheets_dict.items():
            if sheet_df is None or sheet_df.empty:
                continue
            normalized = _normaliser_colonnes_feuille(sheet_df)
            # Tag each row with its ORIGINAL sheet name (one value per sheet).
            normalized[SOURCE_SHEET_COLUMN] = str(sheet_name)
            feuilles.append((str(sheet_name), normalized))

        if not feuilles:
            logger.warning("Toutes les feuilles du fichier Excel sont vides: %s", chemin)
            return pd.DataFrame()

        # 2. Group sheets by their (normalized) schema signature so we can log
        #    which sheets share an identical structure and which differ.
        groupes: dict[frozenset, list[str]] = {}
        for sheet_name, normalized in feuilles:
            signature = frozenset(
                c for c in normalized.columns if c != SOURCE_SHEET_COLUMN
            )
            groupes.setdefault(signature, []).append(sheet_name)

        if len(groupes) == 1:
            logger.info(
                "Excel '%s': %d feuille(s) au schéma identique fusionnée(s): %s",
                chemin,
                len(feuilles),
                ", ".join(name for name, _ in feuilles),
            )
        else:
            for idx, (signature, names) in enumerate(groupes.items(), 1):
                logger.info(
                    "Excel '%s': groupe de schéma %d/%d -> feuilles [%s] "
                    "(%d colonnes communes)",
                    chemin,
                    idx,
                    len(groupes),
                    ", ".join(names),
                    len(signature),
                )
            logger.warning(
                "Excel '%s': %d schémas de feuilles différents détectés. "
                "Les colonnes communes sont alignées; les colonnes propres à "
                "une feuille seront remplies de valeurs manquantes.",
                chemin,
                len(groupes),
            )

        # 3. Concatenate. Because column names are normalized, pandas aligns
        #    matching columns across sheets automatically; the Source_Feuille
        #    column is preserved with one correct value per original sheet.
        df = pd.concat(
            [normalized for _, normalized in feuilles], ignore_index=True
        )

        logger.debug(
            "Excel lu avec moteur '%s' (%d feuilles, %d groupe(s) de schéma): %s",
            engine,
            len(feuilles),
            len(groupes),
            chemin,
        )
        return df
    except Exception as e:
        logger.error("Impossible de lire le fichier Excel %s: %s", chemin, e)
        raise ValueError(
            f"Impossible de lire le fichier Excel. "
            f"Vérifiez que le fichier est valide. Erreur: {e}"
        )
