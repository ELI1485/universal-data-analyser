"""Streamlit dashboard page with premium metrics and activity timeline."""

import streamlit as st
import plotly.graph_objects as go

from app.Http.Controllers.admin_controller import AdminController
from app.Http.Controllers.upload_controller import UploadController
from app.Http.Controllers.report_controller import ReportController
from app.Repositories.audit_repository import AuditRepository
from app.Repositories.anomaly_repository import AnomalyRepository
from resources.views.streamlit.style_utils import render_metric_card

_admin_ctrl = AdminController()
_upload_ctrl = UploadController()
_report_ctrl = ReportController()
_audit_repo = AuditRepository()
_anom_repo = AnomalyRepository()


def render(user_id: int, role: str, nom: str) -> None:
    """Render the enhanced dashboard page with metrics, activity, and quick actions.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
        nom: Current user's name.
    """
    st.markdown(
        "<h2 style='display: flex; align-items: center; gap: 10px;'>"
        "<i class='fa-solid fa-house-chimney'></i> Tableau de bord</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(f"Bienvenue, **{nom}**! Voici un resume de votre activite.")
    st.markdown("---")

    # ── Main Metric Cards ──
    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)
        reports = _report_ctrl.lister_rapports(user_id, role)
        total_anomalies = _anom_repo.count_recent(days=30)
        analyses_count = sum(1 for d in datasets if d.statut == "traite")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_metric_card(
                "Datasets importes", str(len(datasets)), "fa-solid fa-file-csv"
            )
        with col2:
            render_metric_card(
                "Analyses effectuees", str(analyses_count), "fa-solid fa-chart-line"
            )
        with col3:
            render_metric_card(
                "Rapports generes", str(len(reports)), "fa-solid fa-file-pdf"
            )
        with col4:
            render_metric_card(
                "Anomalies (30j)", str(total_anomalies), "fa-solid fa-triangle-exclamation"
            )

    except Exception:
        st.warning("Erreur lors du chargement des metriques.")
        datasets = []
        reports = []
        total_anomalies = 0
        analyses_count = 0

    st.markdown("---")

    # ── Data Quality Overview ──
    if datasets:
        st.markdown(
            "<h3><i class='fa-solid fa-chart-pie'></i> Qualite des donnees</h3>",
            unsafe_allow_html=True,
        )
        _render_data_quality_overview(datasets)
        st.markdown("---")

    # ── Admin: System Stats ──
    if role == "admin":
        st.markdown(
            "<h3><i class='fa-solid fa-building'></i> Statistiques systeme</h3>",
            unsafe_allow_html=True,
        )
        try:
            sys_stats = _admin_ctrl.get_statistiques_systeme()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_metric_card(
                    "Utilisateurs actifs",
                    str(sys_stats["active_users"]),
                    "fa-solid fa-users",
                )
            with col2:
                render_metric_card(
                    "Volume total",
                    f"{sys_stats['total_data_mo']:.1f} Mo",
                    "fa-solid fa-hard-drive",
                )
            with col3:
                render_metric_card(
                    "Total datasets",
                    str(sys_stats["total_datasets"]),
                    "fa-solid fa-database",
                )
            with col4:
                render_metric_card(
                    "Total rapports",
                    str(sys_stats["total_reports"]),
                    "fa-solid fa-clipboard-list",
                )
        except Exception:
            st.warning("Erreur stats systeme.")
        st.markdown("---")

    # ── Activity Timeline ──
    st.markdown(
        "<h3><i class='fa-regular fa-clock'></i> Activite recente</h3>",
        unsafe_allow_html=True,
    )
    _render_activity_timeline(user_id, role)
    st.markdown("---")

    # ── Quick Actions ──
    st.markdown(
        "<h3><i class='fa-solid fa-bolt'></i> Actions rapides</h3>",
        unsafe_allow_html=True,
    )
    _render_quick_actions()


def _render_data_quality_overview(datasets) -> None:
    """Render a data quality overview with gauge charts."""
    # Pick the 3 most recent datasets
    recent = sorted(datasets, key=lambda d: d.cree_le or "", reverse=True)[:3]

    cols = st.columns(len(recent))
    for i, ds in enumerate(recent):
        with cols[i]:
            # Estimate quality based on status
            quality = 95 if ds.statut == "traite" else 70 if ds.statut == "en_traitement" else 50

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=quality,
                title={"text": ds.nom[:25], "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#93DC5C"},
                    "steps": [
                        {"range": [0, 50], "color": "#fee2e2"},
                        {"range": [50, 75], "color": "#fef3c7"},
                        {"range": [75, 100], "color": "#dcfce7"},
                    ],
                    "threshold": {
                        "line": {"color": "#16a34a", "width": 2},
                        "thickness": 0.75,
                        "value": 90,
                    },
                },
                number={"suffix": "%"},
            ))
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=40, b=10),
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"dashboard_quality_gauge_{ds.id}",
            )
            st.caption(
                f"{ds.nb_lignes} lignes - {ds.nb_colonnes} colonnes - {ds.taille_mo:.1f} Mo"
            )


def _render_activity_timeline(user_id: int, role: str) -> None:
    """Render a styled activity timeline from audit logs."""
    try:
        if role == "admin":
            logs = _audit_repo.find_recent(limit=10)
        else:
            logs = _audit_repo.find_by_user(user_id)[:10]

        if not logs:
            st.info("Aucune activite recente.")
            return

        # Custom timeline CSS
        st.markdown("""
        <style>
            .timeline-item {
                display: flex;
                align-items: flex-start;
                gap: 15px;
                padding: 12px 0;
                border-left: 3px solid #93DC5C;
                padding-left: 20px;
                margin-left: 10px;
            }
            .timeline-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-top: 5px;
                flex-shrink: 0;
            }
            .timeline-dot.success { background-color: #22c55e; }
            .timeline-dot.error { background-color: #ef4444; }
            .timeline-content {
                flex: 1;
            }
            .timeline-action {
                font-weight: 600;
                color: #1a1a1a !important;
                font-size: 14px;
            }
            .timeline-meta {
                color: #64748b !important;
                font-size: 12px;
                margin-top: 2px;
            }
        </style>
        """, unsafe_allow_html=True)

        for log in logs:
            dot_class = "success" if log.statut == "succes" else "error"
            timestamp = (
                log.horodatage.strftime("%d/%m/%Y %H:%M")
                if log.horodatage
                else "N/A"
            )
            message = log.message[:80] if log.message else ""

            st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-dot {dot_class}"></div>
                <div class="timeline-content">
                    <div class="timeline-action">{log.action}</div>
                    <div class="timeline-meta">
                        {log.entite} - {timestamp}
                        {f' - {message}' if message else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception:
        st.info("Aucune activite recente disponible.")


def _render_quick_actions() -> None:
    """Render quick action buttons with descriptions (FontAwesome icons)."""
    st.markdown("""
    <style>
        .quick-action-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .quick-action-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
        }
        .quick-action-icon {
            font-size: 32px;
            margin-bottom: 8px;
            color: #93DC5C !important;
        }
        .quick-action-title {
            font-weight: 700;
            color: #1a1a1a !important;
            font-size: 15px;
        }
        .quick-action-desc {
            color: #64748b !important;
            font-size: 12px;
            margin-top: 4px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="quick-action-card">
            <div class="quick-action-icon"><i class="fa-solid fa-folder-open"></i></div>
            <div class="quick-action-title">Importer</div>
            <div class="quick-action-desc">CSV, Excel, XLS</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "Importer un fichier",
            use_container_width=True,
            key="qa_upload",
            icon=":material/upload_file:",
        ):
            st.session_state["current_page"] = "upload"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="quick-action-card">
            <div class="quick-action-icon"><i class="fa-solid fa-chart-pie"></i></div>
            <div class="quick-action-title">Analyser</div>
            <div class="quick-action-desc">Stats, anomalies, IA</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "Lancer une analyse",
            use_container_width=True,
            key="qa_analytics",
            icon=":material/analytics:",
        ):
            st.session_state["current_page"] = "analytics"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="quick-action-card">
            <div class="quick-action-icon"><i class="fa-solid fa-file-pdf"></i></div>
            <div class="quick-action-title">Rapports</div>
            <div class="quick-action-desc">PDF et Excel</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "Generer un rapport",
            use_container_width=True,
            key="qa_report",
            icon=":material/description:",
        ):
            st.session_state["current_page"] = "report"
            st.rerun()

    with col4:
        st.markdown("""
        <div class="quick-action-card">
            <div class="quick-action-icon"><i class="fa-solid fa-code-compare"></i></div>
            <div class="quick-action-title">Comparer</div>
            <div class="quick-action-desc">Drift et schema</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(
            "Comparer des datasets",
            use_container_width=True,
            key="qa_compare",
            icon=":material/compare:",
        ):
            st.session_state["current_page"] = "comparison"
            st.rerun()
