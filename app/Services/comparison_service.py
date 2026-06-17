"""Dataset comparison service for side-by-side analysis.

Compares two datasets to identify schema changes, statistical drift,
and anomaly differences between versions of the same data.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.Repositories.dataset_repository import DatasetRepository
from app.Repositories.anomaly_repository import AnomalyRepository
from app.Services.etl.etl_service import verifier_fichier_dataset

logger = logging.getLogger(__name__)

_dataset_repo = DatasetRepository()
_anomaly_repo = AnomalyRepository()


def comparer_datasets(id_ancien: int, id_nouveau: int) -> dict[str, Any]:
    """Compare two datasets and return a detailed diff report.

    Computes:
    - Schema changes (added, removed, common columns)
    - Row/column count changes
    - Statistical drift per column (mean, median, std shifts)
    - Data type changes
    - Anomaly comparison (new vs. resolved)

    Args:
        id_ancien: The older dataset's ID (baseline).
        id_nouveau: The newer dataset's ID (current).

    Returns:
        A dictionary with comparison results.

    Raises:
        ValueError: If either dataset is not found.
    """
    # Load datasets
    ds_ancien = _dataset_repo.find_by_id(id_ancien)
    ds_nouveau = _dataset_repo.find_by_id(id_nouveau)

    if not ds_ancien:
        raise ValueError(f"Dataset ancien avec ID={id_ancien} introuvable.")
    if not ds_nouveau:
        raise ValueError(f"Dataset nouveau avec ID={id_nouveau} introuvable.")

    logger.info(
        "Comparaison datasets: '%s' (ID=%d) vs '%s' (ID=%d)",
        ds_ancien.nom, id_ancien, ds_nouveau.nom, id_nouveau,
    )

    # Verify both cleaned files still exist for clear, user-friendly errors
    verifier_fichier_dataset(ds_ancien)
    verifier_fichier_dataset(ds_nouveau)

    # Read both files
    try:
        df_ancien = pd.read_csv(ds_ancien.chemin_fichier, encoding="utf-8")
        df_nouveau = pd.read_csv(ds_nouveau.chemin_fichier, encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture des fichiers: {e}")

    # Schema comparison
    schema_changes = _comparer_schema(df_ancien, df_nouveau)

    # Row/column count changes
    taille_changes = {
        "ancien": {"lignes": len(df_ancien), "colonnes": len(df_ancien.columns)},
        "nouveau": {"lignes": len(df_nouveau), "colonnes": len(df_nouveau.columns)},
        "diff_lignes": len(df_nouveau) - len(df_ancien),
        "diff_colonnes": len(df_nouveau.columns) - len(df_ancien.columns),
        "pct_lignes": _safe_pct(len(df_nouveau), len(df_ancien)),
    }

    # Statistical drift on common numeric columns
    common_cols = set(df_ancien.columns) & set(df_nouveau.columns)
    drift_stats = _calculer_drift(df_ancien, df_nouveau, common_cols)

    # Anomaly comparison
    anomaly_comparison = _comparer_anomalies(id_ancien, id_nouveau)

    result = {
        "datasets": {
            "ancien": {
                "id": id_ancien,
                "nom": ds_ancien.nom,
                "nb_lignes": ds_ancien.nb_lignes,
                "nb_colonnes": ds_ancien.nb_colonnes,
            },
            "nouveau": {
                "id": id_nouveau,
                "nom": ds_nouveau.nom,
                "nb_lignes": ds_nouveau.nb_lignes,
                "nb_colonnes": ds_nouveau.nb_colonnes,
            },
        },
        "schema_changes": schema_changes,
        "taille_changes": taille_changes,
        "drift_statistique": drift_stats,
        "anomalies_comparison": anomaly_comparison,
    }

    logger.info(
        "Comparaison terminée: %d colonnes ajoutées, %d supprimées, "
        "%d colonnes avec drift significatif",
        len(schema_changes["colonnes_ajoutees"]),
        len(schema_changes["colonnes_supprimees"]),
        sum(1 for d in drift_stats if d.get("drift_significatif")),
    )

    return result


def _comparer_schema(
    df_ancien: pd.DataFrame, df_nouveau: pd.DataFrame
) -> dict[str, Any]:
    """Compare the schema (column names and types) of two DataFrames.

    Args:
        df_ancien: The older DataFrame.
        df_nouveau: The newer DataFrame.

    Returns:
        A dict with added, removed, common, and type-changed columns.
    """
    cols_ancien = set(df_ancien.columns)
    cols_nouveau = set(df_nouveau.columns)

    colonnes_ajoutees = sorted(cols_nouveau - cols_ancien)
    colonnes_supprimees = sorted(cols_ancien - cols_nouveau)
    colonnes_communes = sorted(cols_ancien & cols_nouveau)

    # Detect type changes in common columns
    types_modifies = []
    for col in colonnes_communes:
        type_ancien = str(df_ancien[col].dtype)
        type_nouveau = str(df_nouveau[col].dtype)
        if type_ancien != type_nouveau:
            types_modifies.append({
                "colonne": col,
                "type_ancien": type_ancien,
                "type_nouveau": type_nouveau,
            })

    return {
        "colonnes_ajoutees": colonnes_ajoutees,
        "colonnes_supprimees": colonnes_supprimees,
        "colonnes_communes": colonnes_communes,
        "types_modifies": types_modifies,
        "nb_ajoutees": len(colonnes_ajoutees),
        "nb_supprimees": len(colonnes_supprimees),
        "nb_communes": len(colonnes_communes),
    }


def _calculer_drift(
    df_ancien: pd.DataFrame,
    df_nouveau: pd.DataFrame,
    common_cols: set[str],
) -> list[dict[str, Any]]:
    """Calculate statistical drift between two DataFrames on common columns.

    Args:
        df_ancien: The older DataFrame.
        df_nouveau: The newer DataFrame.
        common_cols: Set of column names present in both DataFrames.

    Returns:
        A list of drift measurements per column.
    """
    drift_results = []

    for col in sorted(common_cols):
        # Only compare numeric columns
        if not pd.api.types.is_numeric_dtype(df_ancien[col]):
            continue
        if not pd.api.types.is_numeric_dtype(df_nouveau[col]):
            continue

        ancien_stats = {
            "mean": float(df_ancien[col].mean()) if not df_ancien[col].isna().all() else None,
            "median": float(df_ancien[col].median()) if not df_ancien[col].isna().all() else None,
            "std": float(df_ancien[col].std()) if not df_ancien[col].isna().all() else None,
            "min": float(df_ancien[col].min()) if not df_ancien[col].isna().all() else None,
            "max": float(df_ancien[col].max()) if not df_ancien[col].isna().all() else None,
            "null_pct": round(float(df_ancien[col].isna().mean()) * 100, 2),
        }

        nouveau_stats = {
            "mean": float(df_nouveau[col].mean()) if not df_nouveau[col].isna().all() else None,
            "median": float(df_nouveau[col].median()) if not df_nouveau[col].isna().all() else None,
            "std": float(df_nouveau[col].std()) if not df_nouveau[col].isna().all() else None,
            "min": float(df_nouveau[col].min()) if not df_nouveau[col].isna().all() else None,
            "max": float(df_nouveau[col].max()) if not df_nouveau[col].isna().all() else None,
            "null_pct": round(float(df_nouveau[col].isna().mean()) * 100, 2),
        }

        # Calculate drift magnitude
        mean_drift = _safe_diff(nouveau_stats["mean"], ancien_stats["mean"])
        std_drift = _safe_diff(nouveau_stats["std"], ancien_stats["std"])

        # A drift is "significant" if mean shifted by > 1 std
        drift_significatif = False
        if ancien_stats["std"] and ancien_stats["std"] > 0 and mean_drift is not None:
            drift_significatif = abs(mean_drift) > ancien_stats["std"]

        drift_results.append({
            "colonne": col,
            "ancien": ancien_stats,
            "nouveau": nouveau_stats,
            "mean_drift": round(mean_drift, 4) if mean_drift is not None else None,
            "std_drift": round(std_drift, 4) if std_drift is not None else None,
            "mean_pct_change": _safe_pct(
                nouveau_stats["mean"], ancien_stats["mean"]
            ),
            "drift_significatif": drift_significatif,
        })

    return drift_results


def _comparer_anomalies(id_ancien: int, id_nouveau: int) -> dict[str, Any]:
    """Compare anomaly counts between two datasets.

    Args:
        id_ancien: The older dataset ID.
        id_nouveau: The newer dataset ID.

    Returns:
        A dict with anomaly counts for both datasets and the diff.
    """
    try:
        anom_ancien = _anomaly_repo.find_by_dataset(id_ancien)
        anom_nouveau = _anomaly_repo.find_by_dataset(id_nouveau)

        ancien_count = len(anom_ancien)
        nouveau_count = len(anom_nouveau)

        return {
            "ancien_total": ancien_count,
            "nouveau_total": nouveau_count,
            "diff": nouveau_count - ancien_count,
            "amelioration": nouveau_count < ancien_count,
        }
    except Exception:
        return {
            "ancien_total": 0,
            "nouveau_total": 0,
            "diff": 0,
            "amelioration": False,
            "message": "Données d'anomalies non disponibles.",
        }


def _safe_pct(new_val, old_val) -> float:
    """Calculate percentage change safely, handling zeros.

    Args:
        new_val: New value.
        old_val: Old value.

    Returns:
        Percentage change rounded to 2 decimals, or 0.0 if undefined.
    """
    if old_val is None or new_val is None:
        return 0.0
    if old_val == 0:
        return 100.0 if new_val != 0 else 0.0
    return round(((new_val - old_val) / abs(old_val)) * 100, 2)


def _safe_diff(a, b):
    """Safely compute a - b, returning None if either is None."""
    if a is None or b is None:
        return None
    return a - b
