"""Streamlit report generation page."""

import os

import streamlit as st

from app.Http.Controllers.report_controller import ReportController
from app.Http.Controllers.upload_controller import UploadController

_report_ctrl = ReportController()
_upload_ctrl = UploadController()


def render(user_id: int, role: str) -> None:
    """Render the report generation page.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
    """
    st.markdown("<h2 style='display: flex; align-items: center; gap: 10px;'><i class='fa-solid fa-file-pdf'></i> Rapports</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # Dataset selector
    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)
    except Exception as e:
        st.error(f"Erreur chargement datasets: {e}")
        return

    if not datasets:
        st.info("Aucun dataset disponible. Importez d'abord des données.")
        return

    st.markdown("### Générer un nouveau rapport")

    dataset_options = {f"{ds.nom} (ID: {ds.id})": ds.id for ds in datasets}
    selected_label = st.selectbox("Dataset", list(dataset_options.keys()))
    selected_id = dataset_options[selected_label]

    # Format selection
    format_choice = st.radio("Format du rapport", ["PDF", "Excel"], horizontal=True)
    format_value = "pdf" if format_choice == "PDF" else "excel"

    # Generate button
    if st.button("📝 Générer le rapport", use_container_width=True):
        try:
            with st.spinner("Génération du rapport en cours (analyse + mise en page)..."):
                report = _report_ctrl.generer(selected_id, user_id, format_value)

            st.success(
                f"✅ Rapport {format_choice} généré avec succès! "
                f"(Taille: {report.taille_ko:.1f} Ko)"
            )

            # Download button
            if os.path.exists(report.chemin_export):
                with open(report.chemin_export, "rb") as f:
                    file_data = f.read()
                    ext = "pdf" if format_value == "pdf" else "xlsx"
                    mime = (
                        "application/pdf"
                        if format_value == "pdf"
                        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.download_button(
                        label=f"⬇️ Télécharger le rapport ({format_choice})",
                        data=file_data,
                        file_name=f"rapport.{ext}",
                        mime=mime,
                        use_container_width=True,
                    )

        except Exception as e:
            st.error(f"❌ Erreur lors de la génération: {str(e)}")

    st.markdown("---")

    # Past reports
    st.markdown("### 📋 Rapports précédents")
    try:
        reports = _report_ctrl.lister_rapports(user_id, role)

        if not reports:
            st.info("Aucun rapport généré pour le moment.")
            return

        for report in reports:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                icon = "📕" if report.format == "pdf" else "📗"
                st.markdown(f"{icon} Dataset #{report.dataset_id}")
            with col2:
                st.markdown(f"{report.format.upper()}")
            with col3:
                st.markdown(f"{report.taille_ko:.1f} Ko")
            with col4:
                if os.path.exists(report.chemin_export):
                    with open(report.chemin_export, "rb") as f:
                        ext = "pdf" if report.format == "pdf" else "xlsx"
                        mime = (
                            "application/pdf"
                            if report.format == "pdf"
                            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        st.download_button(
                            "⬇️",
                            data=f.read(),
                            file_name=f"rapport_{report.id}.{ext}",
                            mime=mime,
                            key=f"dl_{report.id}",
                        )
                else:
                    st.markdown("*Fichier indisponible*")

    except Exception as e:
        st.error(f"Erreur chargement rapports: {e}")
