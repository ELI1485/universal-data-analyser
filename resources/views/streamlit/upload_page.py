"""Streamlit upload page for dataset import.

Supports multi-file batch import: up to ``MAX_BATCH_FILES`` files at once.
Each file is processed independently through the ETL pipeline so a single
bad file does not abort the rest of the batch.
"""

import os
import tempfile

import streamlit as st

from config.settings import MAX_FILE_SIZE_MB
from app.Http.Controllers.upload_controller import UploadController
from resources.views.streamlit.style_utils import render_metric_card

_upload_ctrl = UploadController()

# Maximum number of files accepted per batch. Stays > 10 per spec.
MAX_BATCH_FILES = 10


def render(user_id: int, role: str) -> None:
    """Render the upload page with file uploader and dataset list.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
    """
    st.markdown(
        "<h2 style='display: flex; align-items: center; gap: 10px;'>"
        "<i class='fa-solid fa-file-import'></i> Importer des donnees</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("### Charger un ou plusieurs fichiers")
    st.caption(
        f"Vous pouvez importer jusqu'a {MAX_BATCH_FILES} fichiers en un seul "
        f"lot. Taille maximale par fichier : {MAX_FILE_SIZE_MB} Mo. "
        "Formats acceptes : CSV, Excel (.xlsx, .xls)."
    )

    uploaded_files = st.file_uploader(
        f"Selectionnez jusqu'a {MAX_BATCH_FILES} fichiers",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help=(
            f"Formats acceptes: CSV, Excel (.xlsx, .xls). "
            f"Maximum {MAX_BATCH_FILES} fichiers par lot."
        ),
    )

    # Cap to MAX_BATCH_FILES if the user selected more
    if uploaded_files and len(uploaded_files) > MAX_BATCH_FILES:
        st.warning(
            f"Vous avez selectionne {len(uploaded_files)} fichiers. "
            f"Seuls les {MAX_BATCH_FILES} premiers seront traites."
        )
        uploaded_files = uploaded_files[:MAX_BATCH_FILES]

    name_prefix = st.text_input(
        "Prefixe de nom (optionnel)",
        placeholder="Ex: Ventes Q4 2024",
        help=(
            "Si renseigne, chaque dataset sera nomme '<prefixe> - <nom du fichier>'. "
            "Sinon, le nom du fichier (sans extension) est utilise."
        ),
    )

    is_disabled = not uploaded_files
    if st.button(
        "Importer et traiter",
        disabled=is_disabled,
        icon=":material/upload:",
        use_container_width=True,
    ):
        if not uploaded_files:
            st.error("Veuillez selectionner au moins un fichier.")
            return

        _process_batch(uploaded_files, name_prefix, user_id)

    st.markdown("---")

    # Existing datasets table
    st.markdown(
        "<h3><i class='fa-solid fa-list'></i> Mes datasets</h3>",
        unsafe_allow_html=True,
    )

    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)

        if not datasets:
            st.info("Aucun dataset importe pour le moment.")
            return

        for ds in datasets:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            with col1:
                st.markdown(f"**{ds.nom}**")
            with col2:
                st.markdown(f"{ds.nb_lignes} lignes, {ds.nb_colonnes} cols")
            with col3:
                if ds.statut == "traite":
                    icon_html = (
                        "<span style='color:#22c55e;'>"
                        "<i class='fa-solid fa-circle-check'></i></span>"
                    )
                else:
                    icon_html = (
                        "<span style='color:#f59e0b;'>"
                        "<i class='fa-regular fa-clock'></i></span>"
                    )
                st.markdown(f"{icon_html} {ds.statut}", unsafe_allow_html=True)
            with col4:
                st.markdown(f"{ds.taille_mo:.2f} Mo")
            with col5:
                if st.button(
                    "",
                    key=f"del_{ds.id}",
                    icon=":material/delete:",
                    help="Supprimer ce dataset",
                ):
                    try:
                        _upload_ctrl.supprimer_dataset(ds.id, user_id, role)
                        st.success(f"Dataset '{ds.nom}' supprime.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

    except Exception as e:
        st.error(f"Erreur lors du chargement des datasets: {e}")


def _process_batch(uploaded_files: list, name_prefix: str, user_id: int) -> None:
    """Run the ETL pipeline on each uploaded file independently.

    A failure on one file does not abort the rest of the batch. A summary
    of successes and failures is shown at the end.

    Args:
        uploaded_files: List of ``UploadedFile`` objects from ``st.file_uploader``.
        name_prefix: Optional prefix prepended to each generated dataset name.
        user_id: Current user's ID.
    """
    successes: list[dict] = []
    failures: list[dict] = []
    total = len(uploaded_files)

    progress = st.progress(0.0, text=f"0 / {total} fichier(s) traite(s)...")

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        progress.progress(
            (idx - 1) / total,
            text=f"Traitement de '{uploaded_file.name}' ({idx}/{total})...",
        )

        # Build dataset name
        base_name = uploaded_file.name.rsplit(".", 1)[0]
        dataset_name = f"{name_prefix} - {base_name}" if name_prefix else base_name

        # Size check
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            failures.append({
                "file": uploaded_file.name,
                "error": (
                    f"Fichier trop volumineux ({file_size_mb:.1f} Mo > "
                    f"{MAX_FILE_SIZE_MB} Mo)"
                ),
            })
            continue

        # Save to temp file
        tmp_path = None
        try:
            ext = uploaded_file.name.rsplit(".", 1)[-1]
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{ext}"
            ) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            dataset = _upload_ctrl.importer_fichier(tmp_path, dataset_name, user_id)
            successes.append({
                "file": uploaded_file.name,
                "dataset_name": dataset_name,
                "dataset": dataset,
            })

        except Exception as e:
            failures.append({"file": uploaded_file.name, "error": str(e)})
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    progress.progress(1.0, text=f"{total}/{total} fichier(s) traite(s).")

    # ── Summary ──
    if successes:
        st.success(
            f"{len(successes)} fichier(s) importe(s) avec succes "
            f"sur {total}."
        )
    if failures:
        st.error(f"{len(failures)} fichier(s) en echec sur {total}.")

    if successes:
        st.markdown(
            "<h4><i class='fa-solid fa-circle-check'></i> Imports reussis</h4>",
            unsafe_allow_html=True,
        )
        for s in successes:
            ds = s["dataset"]
            with st.expander(f"{s['dataset_name']} ({s['file']})"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    render_metric_card(
                        "Lignes", str(ds.nb_lignes), "fa-solid fa-list-ol"
                    )
                with col2:
                    render_metric_card(
                        "Colonnes", str(ds.nb_colonnes), "fa-solid fa-table-columns"
                    )
                with col3:
                    render_metric_card(
                        "Taille", f"{ds.taille_mo:.2f} Mo", "fa-solid fa-database"
                    )
                with col4:
                    render_metric_card(
                        "Statut", ds.statut, "fa-solid fa-check-double"
                    )

                quality_report = getattr(ds, "_quality_report", None)
                if quality_report:
                    st.markdown("**Rapport de qualite**")
                    qc1, qc2, qc3 = st.columns(3)
                    with qc1:
                        render_metric_card(
                            "Doublons supprimes",
                            str(quality_report.get("doublons_supprimes", 0)),
                            "fa-solid fa-clone",
                        )
                    with qc2:
                        render_metric_card(
                            "Valeurs nulles remplies",
                            str(quality_report.get("valeurs_nulles_remplies", 0)),
                            "fa-solid fa-bandage",
                        )
                    with qc3:
                        render_metric_card(
                            "Taux de completude",
                            f"{quality_report.get('taux_completude', 0):.1f}%",
                            "fa-solid fa-percent",
                        )

    if failures:
        st.markdown(
            "<h4><i class='fa-solid fa-circle-xmark'></i> Imports en echec</h4>",
            unsafe_allow_html=True,
        )
        for f in failures:
            st.markdown(f"- **{f['file']}** : {f['error']}")
