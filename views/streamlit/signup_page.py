"""Streamlit signup page."""

import streamlit as st

from controllers.auth_controller import AuthController

_auth_ctrl = AuthController()


def render() -> None:
    """Render the signup page with name, email, and password fields."""
    # Center the signup form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("")
        st.markdown("")
        st.markdown("## 📊 Universal Data Analyzer")
        st.markdown("### Création de compte")
        st.markdown("---")

        # Signup form
        with st.form("signup_form"):
            nom = st.text_input(
                "Nom complet",
                placeholder="Jean Dupont",
                key="signup_nom",
            )
            email = st.text_input(
                "Email",
                placeholder="jean.dupont@example.com",
                key="signup_email",
            )
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Choisissez un mot de passe sécurisé",
                key="signup_password",
            )
            confirm_password = st.text_input(
                "Confirmer le mot de passe",
                type="password",
                placeholder="Confirmez votre mot de passe",
                key="signup_confirm_password",
            )

            submitted = st.form_submit_button(
                "S'inscrire", use_container_width=True
            )

        if submitted:
            if not nom or not email or not password or not confirm_password:
                st.error("Veuillez remplir tous les champs.")
            elif password != confirm_password:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(password) < 8:
                st.error("Le mot de passe doit contenir au moins 8 caractères.")
            else:
                try:
                    _auth_ctrl.register(nom, email, password, ip="127.0.0.1")
                    st.success("✅ Compte créé avec succès! Vous pouvez maintenant vous connecter.")
                    
                    # Store message to show on login page if needed, or just redirect
                    if st.button("Aller à la page de connexion"):
                        st.session_state["current_page"] = "login"
                        st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
                except Exception as e:
                    st.error(f"Erreur inattendue: {str(e)}")

        # Link to login
        st.markdown("---")
        if st.button("Déjà un compte ? Se connecter"):
            st.session_state["current_page"] = "login"
            st.rerun()
