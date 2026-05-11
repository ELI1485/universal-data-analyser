"""Streamlit dashboard page."""

import streamlit as st

from controllers.admin_controller import AdminController
from controllers.upload_controller import UploadController
from controllers.report_controller import ReportController
from repositories.audit_repository import AuditRepository

_admin_ctrl = AdminController()
_upload_ctrl = UploadController()
_report_ctrl = ReportController()
_audit_repo = AuditRepository()


def render(user_id: int, role: str, nom: str) -> None:
    """Render the dashboard page with metrics and recent activity.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
        nom: Current user's name.
    """
    st.markdown(f"## 🏠 Tableau de bord")
    st.markdown(f"Bienvenue, **{nom}**!")
    st.markdown("---")

    # Metric cards
    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)
        reports = _report_ctrl.lister_rapports(user_id, role)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📁 Datasets",
                value=len(datasets),
            )
        with col2:
            analyses_count = sum(1 for d in datasets if d.statut == "traite")
            st.metric(
                label="📈 Analyses effectuées",
                value=analyses_count,
            )
        with col3:
            st.metric(
                label="📄 Rapports générés",
                value=len(reports),
            )
        with col4:
            total_anomalies = 0
            from repositories.anomaly_repository import AnomalyRepository
            _anom_repo = AnomalyRepository()
            total_anomalies = _anom_repo.count_recent(days=30)
            st.metric(
                label="⚠️ Anomalies (30j)",
                value=total_anomalies,
            )

    except Exception as e:
        st.warning(f"Erreur lors du chargement des métriques: {e}")

    st.markdown("---")

    # Admin: system stats
    if role == "admin":
        st.markdown("### 📊 Statistiques système")
        try:
            sys_stats = _admin_ctrl.get_statistiques_systeme()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Utilisateurs actifs", sys_stats["active_users"])
            with col2:
                st.metric("Total données (Mo)", f"{sys_stats['total_data_mo']:.1f}")
            with col3:
                st.metric("Total datasets", sys_stats["total_datasets"])
            with col4:
                st.metric("Total rapports", sys_stats["total_reports"])
        except Exception as e:
            st.warning(f"Erreur stats système: {e}")
        st.markdown("---")

    # Recent activity
    st.markdown("### 🕐 Activité récente")
    try:
        if role == "admin":
            logs = _audit_repo.find_recent(limit=5)
        else:
            logs = _audit_repo.find_by_user(user_id)[:5]

        if logs:
            for log in logs:
                icon = "✅" if log.statut == "succes" else "❌"
                timestamp = log.horodatage.strftime("%d/%m/%Y %H:%M") if log.horodatage else "N/A"
                st.markdown(
                    f"{icon} **{log.action}** — {log.entite} "
                    f"— {timestamp}"
                )
        else:
            st.info("Aucune activité récente.")
    except Exception as e:
        st.info("Aucune activité récente disponible.")

    st.markdown("---")

    # Quick actions
    st.markdown("### ⚡ Actions rapides")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Importer un fichier", use_container_width=True):
            st.session_state["current_page"] = "upload"
            st.rerun()
    with col2:
        if st.button("📈 Voir mes analyses", use_container_width=True):
            st.session_state["current_page"] = "analytics"
            st.rerun()
