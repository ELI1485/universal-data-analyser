"""Streamlit admin page for system administration."""

import streamlit as st

from app.Http.Controllers.admin_controller import AdminController

_admin_ctrl = AdminController()


def render() -> None:
    """Render the admin page. Only accessible to admin users."""
    if st.session_state.get("role") != "admin":
        st.error("Accès refusé. Cette page est réservée aux administrateurs.")
        return

    st.markdown("## ⚙️ Administration")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Tableau de bord", "👥 Utilisateurs", "📋 Logs d'audit", "🔧 Configuration"]
    )

    with tab1:
        _render_admin_dashboard()

    with tab2:
        _render_users_tab()

    with tab3:
        _render_audit_tab()

    with tab4:
        _render_config_tab()


def _render_admin_dashboard() -> None:
    """Render the admin dashboard with system metrics."""
    st.markdown("### Statistiques système")

    try:
        stats = _admin_ctrl.get_statistiques_systeme()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Utilisateurs totaux", stats["total_users"])
            st.metric("Utilisateurs actifs", stats["active_users"])
        with col2:
            st.metric("Analyses effectuées", stats["total_analyses"])
            st.metric("Rapports générés", stats["total_reports"])
        with col3:
            st.metric("Volume de données (Mo)", f"{stats['total_data_mo']:.1f}")
            st.metric("Anomalies (30 jours)", stats["anomalies_30j"])

    except Exception as e:
        st.error(f"Erreur: {e}")


def _render_users_tab() -> None:
    """Render the users management tab."""
    st.markdown("### Gestion des utilisateurs")

    # List users
    try:
        users = _admin_ctrl.lister_utilisateurs()

        if users:
            for user in users:
                col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 2])
                with col1:
                    st.markdown(f"**{user.nom}**")
                with col2:
                    st.markdown(user.email)
                with col3:
                    st.markdown(user.role)
                with col4:
                    icon = "🟢" if user.statut == "actif" else "🔴"
                    st.markdown(f"{icon} {user.statut}")
                with col5:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("⏸️", key=f"deact_{user.id}", help="Désactiver"):
                            try:
                                _admin_ctrl.desactiver_utilisateur(user.id)
                                st.success(f"Utilisateur '{user.nom}' désactivé.")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                    with c2:
                        if st.button("🔑", key=f"reset_{user.id}", help="Reset mdp"):
                            try:
                                _admin_ctrl.reinitialiser_mdp(user.id, "NewPass123!")
                                st.success("Mot de passe réinitialisé: NewPass123!")
                            except Exception as e:
                                st.error(str(e))
                    with c3:
                        if st.button("🗑️", key=f"del_user_{user.id}", help="Supprimer"):
                            try:
                                _admin_ctrl.supprimer_utilisateur(user.id)
                                st.success(f"Utilisateur supprimé.")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
    except Exception as e:
        st.error(f"Erreur: {e}")

    # Create user form
    st.markdown("---")
    st.markdown("### Créer un utilisateur")

    with st.form("create_user_form"):
        nom = st.text_input("Nom complet")
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        role = st.selectbox("Rôle", ["analyste", "admin"])
        submitted = st.form_submit_button("Créer l'utilisateur")

    if submitted:
        if not all([nom, email, password]):
            st.error("Tous les champs sont obligatoires.")
        else:
            try:
                user = _admin_ctrl.creer_utilisateur(nom, email, password, role)
                st.success(f"✅ Utilisateur '{nom}' créé avec succès!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Erreur: {e}")


def _render_audit_tab() -> None:
    """Render the audit logs tab."""
    st.markdown("### Logs d'audit")

    try:
        logs = _admin_ctrl.get_audit_logs(limit=50)

        if logs:
            import pandas as pd
            log_data = []
            for log in logs:
                log_data.append({
                    "Date": log.horodatage.strftime("%d/%m/%Y %H:%M") if log.horodatage else "N/A",
                    "User ID": log.user_id or "Système",
                    "Action": log.action,
                    "Entité": log.entite,
                    "Statut": log.statut,
                    "Message": (log.message or "")[:80],
                })
            df = pd.DataFrame(log_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun log d'audit disponible.")
    except Exception as e:
        st.error(f"Erreur: {e}")

    # Error logs
    st.markdown("### ❌ Logs d'erreurs")
    try:
        error_logs = _admin_ctrl.get_error_logs(limit=20)
        if error_logs:
            for log in error_logs:
                timestamp = log.horodatage.strftime("%d/%m/%Y %H:%M") if log.horodatage else "N/A"
                st.error(f"{timestamp} — {log.action}: {log.message}")
        else:
            st.success("Aucune erreur récente.")
    except Exception as e:
        st.error(f"Erreur: {e}")


def _render_config_tab() -> None:
    """Render the configuration tab."""
    st.markdown("### Configuration")

    st.markdown("#### LLM (Gemini)")
    from config.settings import LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
    st.text_input("Modèle", value=LLM_MODEL, disabled=True)
    st.number_input("Température", value=LLM_TEMPERATURE, disabled=True)
    st.number_input("Max tokens", value=LLM_MAX_TOKENS, disabled=True)

    if st.button("🔌 Tester connexion LLM"):
        try:
            from app.Services.llm_service import LLMService
            llm = LLMService()
            success = llm.test_connection()
            if success:
                st.success("✅ Connexion LLM fonctionnelle!")
            else:
                st.warning("⚠️ Connexion LLM non disponible. Vérifiez la clé API.")
        except Exception as e:
            st.error(f"Erreur: {e}")

    st.markdown("#### Seuils de détection d'anomalies")
    st.number_input("Seuil Z-Score", value=3.0, disabled=True)
    st.number_input("Facteur IQR", value=1.5, disabled=True)
    st.number_input("Contamination Isolation Forest", value=0.05, disabled=True)
    st.info("Pour modifier ces paramètres, éditez le fichier .env")
