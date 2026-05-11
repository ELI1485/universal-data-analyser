"""Streamlit login page."""

import streamlit as st

from controllers.auth_controller import AuthController

_auth_ctrl = AuthController()


def render() -> None:
    """Render the login page with email and password fields."""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("")
        st.markdown("")
        st.markdown("## 📊 Universal Data Analyzer")
        st.markdown("### Connexion")
        st.markdown("---")

        # Login form
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                placeholder="admin@uda.local",
                key="login_email",
            )
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Entrez votre mot de passe",
                key="login_password",
            )

            submitted = st.form_submit_button(
                "Se connecter", use_container_width=True
            )

        if submitted:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
                return

            try:
                result = _auth_ctrl.login(email, password, ip="127.0.0.1")

                # Store in session state
                st.session_state["token"] = result["token"]
                st.session_state["user_id"] = result["user_id"]
                st.session_state["role"] = result["role"]
                st.session_state["nom"] = result["nom"]
                st.session_state["current_page"] = "dashboard"

                st.success(f"Bienvenue, {result['nom']}!")
                st.rerun()

            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except PermissionError as e:
                st.warning(f"⚠️ {str(e)}")
            except Exception as e:
                st.error(f"Erreur inattendue: {str(e)}")

        # Signup link
        st.markdown("---")
        if st.button("Pas encore de compte ? S'inscrire"):
            st.session_state["current_page"] = "signup"
            st.rerun()

        # Help text
        st.markdown("---")
        st.markdown(
            "<small>Compte par défaut: admin@uda.local / Admin1234!</small>",
            unsafe_allow_html=True,
        )
