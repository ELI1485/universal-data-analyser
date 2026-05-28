"""Streamlit signup page."""

import streamlit as st

from app.Http.Controllers.auth_controller import AuthController

_auth_ctrl = AuthController()


def render() -> None:
    """Render the signup page as a full-page overlay for exact layout fidelity."""
    
    # Aggressive CSS to hide Streamlit's default structure and force our design
    st.markdown(
        """
        <style>
        /* 1. Reset Streamlit App Shell */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #93DC5C 0%, #4e732d 100%) !important;
        }
        [data-testid="stHeader"], [data-testid="stSidebar"], .stDeployButton {
            display: none !important;
        }
        [data-testid="stMain"] > div {
            padding: 0 !important;
        }
        
        /* 2. Create the Centered Viewport */
        .viewport {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        /* 3. The Main Authentication Card */
        .auth-card {
            display: flex;
            width: 1100px;
            max-width: 95vw;
            height: 650px;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }

        /* 4. Left Panel - Image and Logo Box */
        .auth-left {
            flex: 1.2;
            background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2015&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .auth-left::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.3);
        }
        .auth-logo-box {
            position: relative;
            z-index: 10;
            background: rgba(147, 220, 92, 0.95);
            padding: 30px;
            border-radius: 25px;
            text-align: center;
            width: 220px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        /* 5. Right Panel - The Form */
        .auth-right {
            flex: 1;
            background: white;
            padding: 40px 60px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .auth-title {
            font-size: 1.8rem;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-weight: 300;
        }

        /* 6. Form Styling Overrides */
        .stTextInput input {
            border-radius: 50px !important;
            height: 48px !important;
            border: 1px solid #e0e0e0 !important;
            background: #f8f9fc !important;
            padding-left: 20px !important;
            font-size: 0.95rem !important;
        }
        .stTextInput input:focus {
            border-color: #93DC5C !important;
            background: white !important;
        }
        
        div.stButton > button {
            border-radius: 50px !important;
            height: 50px !important;
            background: #93DC5C !important;
            color: white !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            border: none !important;
            margin-top: 15px;
            transition: all 0.3s ease !important;
        }
        div.stButton > button:hover {
            background: #7ab84d !important;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(147, 220, 92, 0.3) !important;
        }

        /* Links and Footer */
        .auth-links {
            text-align: center;
            margin-top: 20px;
        }
        .auth-links a {
            color: #4e73df;
            text-decoration: none;
            font-size: 0.85rem;
            display: block;
            margin-bottom: 5px;
        }
        .auth-footer {
            text-align: center;
            color: #a0a0a0;
            font-size: 0.8rem;
            margin-top: 30px;
        }

        /* Remove Streamlit default gap/margins */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Full-page Viewport
    st.markdown("<div class='viewport'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    
    # Left Half
    st.markdown(
        """
        <div class='auth-left'>
            <div class='auth-logo-box'>
                <img src='https://cdn-icons-png.flaticon.com/512/2103/2103633.png' width='90'><br>
                <span style='color: white; font-weight: bold; font-size: 1.2rem; letter-spacing: 1px;'>Bienvenue</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Right Half
    st.markdown("<div class='auth-right'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-title'>Inscription</div>", unsafe_allow_html=True)

    with st.form("signup_form", clear_on_submit=False):
        nom = st.text_input("Nom complet", placeholder="Jean Dupont", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="jean.dupont@example.com", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        password = st.text_input("Mot de passe", type="password", placeholder="••••••••••••", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        confirm_password = st.text_input("Confirmer le mot de passe", type="password", placeholder="••••••••••••", label_visibility="collapsed")
        
        submitted = st.form_submit_button("S'inscrire", use_container_width=True)

    if submitted:
        if nom and email and password and confirm_password:
            if password != confirm_password:
                st.error("Les mots de passe ne correspondent pas")
            else:
                try:
                    _auth_ctrl.register(nom, email, password, ip="127.0.0.1")
                    st.success("Compte créé avec succès!")
                    st.session_state["current_page"] = "login"
                    st.rerun()
                except Exception:
                    st.error("Erreur lors de l'inscription")
        else:
            st.error("Veuillez remplir tous les champs")

    st.markdown(
        """
        <div class='auth-links'>
            <a href='#' onClick='window.location.reload()'>Déjà un compte ? Se connecter</a>
        </div>
        <div class='auth-footer'>Copyright © 2026 - Tous droits réservés</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True) # Close auth-right
    st.markdown("</div>", unsafe_allow_html=True) # Close auth-card
    st.markdown("</div>", unsafe_allow_html=True) # Close viewport
