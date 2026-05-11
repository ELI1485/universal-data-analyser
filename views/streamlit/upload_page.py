"""Streamlit upload page for dataset import."""

import os
import tempfile

import streamlit as st

from config.settings import MAX_FILE_SIZE_MB
from controllers.upload_controller import UploadController

_upload_ctrl = UploadController()


def render(user_id: int, role: str) -> None:
    """Render the upload page with file uploader and dataset list.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
    """
    st.markdown("## 📁 Importer des données")
    st.markdown("---")

    # File upload section
    st.markdown("### Charger un nouveau fichier")

    uploaded_file = st.file_uploader(
        f"Sélectionnez un fichier (max {MAX_FILE_SIZE_MB} Mo)",
        type=["csv", "xlsx", "xls"],
        help="Formats acceptés: CSV, Excel (.xlsx, .xls)",
    )

    dataset_name = st.text_input(
        "Nom du dataset",
        placeholder="Ex: Ventes Q4 2024",
        help="Nom d'affichage pour identifier ce dataset",
    )

    if st.button("📤 Importer et traiter", disabled=uploaded_file is None):
        if uploaded_file is None:
            st.error("Veuillez sélectionner un fichier.")
            return

        if not dataset_name:
            dataset_name = uploaded_file.name.rsplit(".", 1)[0]

        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"Fichier trop volumineux ({file_size_mb:.1f} Mo). "
                f"Taille maximale: {MAX_FILE_SIZE_MB} Mo."
            )
            return

        # Save to temp file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{uploaded_file.name.rsplit('.', 1)[-1]}"
        ) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        # Run ETL pipeline
        try:
            with st.spinner("Traitement en cours (ingestion, validation, nettoyage)..."):
                dataset = _upload_ctrl.importer_fichier(tmp_path, dataset_name, user_id)

            st.success(f"✅ Dataset '{dataset_name}' importé avec succès!")

            # Show quality report if available
            quality_report = getattr(dataset, "_quality_report", None)
            if quality_report:
                st.markdown("#### 📋 Rapport de qualité")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Lignes", quality_report.get("lignes_finales", 0))
                with col2:
                    st.metric("Colonnes", quality_report.get("colonnes_finales", 0))
                with col3:
                    st.metric(
                        "Doublons supprimés",
                        quality_report.get("doublons_supprimes", 0),
                    )
                with col4:
                    st.metric(
                        "Nulls remplis",
                        quality_report.get("valeurs_nulles_remplies", 0),
                    )

                st.metric(
                    "Taux de complétude",
                    f"{quality_report.get('taux_completude', 0):.1f}%",
                )
            else:
                st.info(
                    f"Dataset créé: {dataset.nb_lignes} lignes, "
                    f"{dataset.nb_colonnes} colonnes"
                )

        except Exception as e:
            st.error(f"❌ Erreur lors de l'importation: {str(e)}")
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    st.markdown("---")

    # Existing datasets table
    st.markdown("### 📋 Mes datasets")

    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)

        if not datasets:
            st.info("Aucun dataset importé pour le moment.")
            return

        for ds in datasets:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            with col1:
                st.markdown(f"**{ds.nom}**")
            with col2:
                st.markdown(f"{ds.nb_lignes} lignes, {ds.nb_colonnes} cols")
            with col3:
                status_icon = "✅" if ds.statut == "traite" else "⏳"
                st.markdown(f"{status_icon} {ds.statut}")
            with col4:
                st.markdown(f"{ds.taille_mo:.2f} Mo")
            with col5:
                if st.button("🗑️", key=f"del_{ds.id}"):
                    try:
                        _upload_ctrl.supprimer_dataset(ds.id, user_id, role)
                        st.success(f"Dataset '{ds.nom}' supprimé.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {e}")

    except Exception as e:
        st.error(f"Erreur lors du chargement des datasets: {e}")
