"""Main Streamlit application entry point.

Handles routing based on session state and provides navigation.
Run with: streamlit run views/streamlit/app.py
"""

import sys
from pathlib import Path

# Add project root to path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
st.write("Application démarre...")

from config.logging_config import setup_logging
from config.settings import LOG_DIR, LOG_LEVEL

# Initialize logging on first run
if "logging_initialized" not in st.session_state:
    setup_logging(log_dir=LOG_DIR, log_level=LOG_LEVEL)
    st.session_state["logging_initialized"] = True

# Import page modules
from views.streamlit.login_page import render as render_login
from views.streamlit.dashboard_page import render as render_dashboard
from views.streamlit.upload_page import render as render_upload
from views.streamlit.analytics_page import render as render_analytics
from views.streamlit.report_page import render as render_report
from views.streamlit.admin_page import render as render_admin
from views.streamlit.signup_page import render as render_signup


def main() -> None:
    """Main application entry point with routing logic."""
    st.set_page_config(
        page_title="Universal Data Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "nom" not in st.session_state:
        st.session_state["nom"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "login"

    # Route based on authentication
    if not st.session_state["token"]:
        if st.session_state["current_page"] == "signup":
            render_signup()
        else:
            render_login()
    else:
        _render_authenticated_app()


def _render_authenticated_app() -> None:
    """Render the main application for authenticated users."""
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 📊 Universal Data Analyzer")
        st.markdown(f"**Utilisateur:** {st.session_state['nom']}")
        st.markdown(f"**Rôle:** {st.session_state['role'].capitalize()}")
        st.divider()

        # Navigation buttons
        if st.button("🏠 Tableau de bord", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            st.rerun()

        if st.button("📁 Importer des données", use_container_width=True):
            st.session_state["current_page"] = "upload"
            st.rerun()

        if st.button("📈 Analyses", use_container_width=True):
            st.session_state["current_page"] = "analytics"
            st.rerun()

        if st.button("📄 Rapports", use_container_width=True):
            st.session_state["current_page"] = "report"
            st.rerun()

        if st.session_state["role"] == "admin":
            if st.button("⚙️ Administration", use_container_width=True):
                st.session_state["current_page"] = "admin"
                st.rerun()

        st.divider()

        if st.button("🚪 Déconnexion", use_container_width=True):
            _logout()

    # Route to the selected page
    page = st.session_state["current_page"]

    if page == "dashboard":
        render_dashboard(
            st.session_state["user_id"],
            st.session_state["role"],
            st.session_state["nom"],
        )
    elif page == "upload":
        render_upload(st.session_state["user_id"], st.session_state["role"])
    elif page == "analytics":
        render_analytics(st.session_state["user_id"], st.session_state["role"])
    elif page == "report":
        render_report(st.session_state["user_id"], st.session_state["role"])
    elif page == "admin":
        if st.session_state["role"] == "admin":
            render_admin()
        else:
            st.error("Accès refusé. Cette page est réservée aux administrateurs.")
    else:
        render_dashboard(
            st.session_state["user_id"],
            st.session_state["role"],
            st.session_state["nom"],
        )


def _logout() -> None:
    """Clear session state and redirect to login."""
    from controllers.auth_controller import AuthController

    auth_ctrl = AuthController()
    try:
        auth_ctrl.logout(st.session_state["token"])
    except Exception:
        pass

    st.session_state["token"] = None
    st.session_state["user_id"] = None
    st.session_state["role"] = None
    st.session_state["nom"] = None
    st.session_state["current_page"] = "dashboard"
    st.rerun()


if __name__ == "__main__":
    main()
