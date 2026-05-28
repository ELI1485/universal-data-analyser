"""Streamlit login page."""

import streamlit as st

from app.Http.Controllers.auth_controller import AuthController

_auth_ctrl = AuthController()


def render() -> None:
    """Render the login page with the original green-themed split card."""

    # ── CSS ────────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap');

        /* 1. Global Reset & Background */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #93DC5C 0%, #4e732d 100%) !important;
            font-family: 'Nunito', sans-serif !important;
        }
        [data-testid="stHeader"], [data-testid="stSidebar"],
        .stDeployButton, [data-testid="stToolbar"] {
            display: none !important;
        }
        
        /* Center the main container */
        [data-testid="stMain"] {
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* 2. Make the block container the card itself */
        .block-container {
            padding: 0 !important;
            max-width: 1100px !important;
            width: 100% !important;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.30);
            overflow: hidden;
            margin-top: 5vh;
            margin-bottom: 5vh;
        }

        /* 3. Style the columns */
        /* Left Column - Image & Logo */
        [data-testid="column"]:nth-of-type(1) {
            background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2015&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            position: relative;
            min-height: 620px;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 0 !important;
            margin: 0 !important;
            width: 55% !important;
        }
        [data-testid="column"]:nth-of-type(1)::after {
            content: '';
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.25);
        }
        
        /* The logo box needs to be rendered via markdown in col1, bring it to front */
        .auth-logo-box {
            position: relative;
            z-index: 2;
            background: rgba(147, 220, 92, 0.95);
            padding: 28px 32px;
            border-radius: 22px;
            text-align: center;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
            margin: auto;
        }
        .auth-logo-box img { width: 85px; display: block; margin: 0 auto 8px; }
        .auth-logo-box .brand {
            color: #fff;
            font-weight: 700;
            font-size: 1.25rem;
            letter-spacing: 1px;
        }

        /* Right Column - Form Area */
        [data-testid="column"]:nth-of-type(2) {
            padding: 60px 50px !important;
            width: 45% !important;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        /* 4. Title */
        .auth-form-title {
            font-family: 'Nunito', sans-serif;
            font-size: 1.65rem;
            font-weight: 300;
            color: #5a5c69;
            text-align: center;
            margin-bottom: 30px;
            margin-top: 0;
        }

        /* 5. Form inputs (Pill shaped, specific paddings & font sizes) */
        .stTextInput > div > div > input {
            font-size: 0.8rem !important;
            border-radius: 10rem !important;
            padding: 1.5rem 1rem !important;
            height: auto !important;
            border: 1px solid #d1d3e2 !important;
            background-color: #ffffff !important;
            font-family: 'Nunito', sans-serif !important;
            color: #6e707e !important;
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #93DC5C !important;
            box-shadow: 0 0 0 0.2rem rgba(147, 220, 92, 0.25) !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #858796 !important;
        }

        /* 6. Checkbox */
        .stCheckbox {
            padding-left: 0.5rem;
        }
        .stCheckbox label {
            line-height: 1.5rem !important;
            font-family: 'Nunito', sans-serif !important;
        }
        .stCheckbox label span {
            font-size: 0.85rem !important;
            color: #858796 !important;
        }

        /* 7. Submit button (Pill shaped) */
        [data-testid="stFormSubmitButton"] > button {
            font-size: 0.8rem !important;
            border-radius: 10rem !important;
            padding: 0.75rem 1rem !important;
            height: auto !important;
            background-color: #93DC5C !important;
            color: #fff !important;
            font-weight: 600 !important;
            font-family: 'Nunito', sans-serif !important;
            border: none !important;
            transition: all 0.2s ease !important;
            letter-spacing: 0.3px !important;
            margin-top: 15px !important;
        }
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #7ab84d !important;
            box-shadow: 0 4px 14px rgba(147, 220, 92, 0.35) !important;
        }

        /* 8. Links and footer */
        .auth-links { text-align: center; margin-top: 20px; }
        .auth-links a {
            color: #4e73df;
            text-decoration: none;
            font-size: 0.8rem;
            font-family: 'Nunito', sans-serif;
            display: block;
            margin-bottom: 8px;
        }
        .auth-links a:hover { color: #224abe; text-decoration: underline; }
        .auth-footer {
            text-align: center;
            color: #858796;
            font-size: 0.8rem;
            font-family: 'Nunito', sans-serif;
            margin-top: 28px;
        }

        /* 9. Responsive adjustments */
        @media (max-width: 1000px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column;
            }
            [data-testid="column"]:nth-of-type(1) {
                display: none !important;
            }
            [data-testid="column"]:nth-of-type(2) {
                width: 100% !important;
                padding: 40px 30px !important;
            }
            .block-container {
                max-width: 500px !important;
                margin-top: 10vh;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Layout ──────────────────────────────────────────────────────
    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown(
            """
            <div style="height: 100%; display: flex; align-items: center; justify-content: center;">
                <div class="auth-logo-box">
                    <img src="https://cdn-icons-png.flaticon.com/512/2103/2103633.png" alt="UDA">
                    <span class="brand">UDA Portal</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown('<p class="auth-form-title">Plateforme eServices</p>', unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Identifiant", placeholder="Ex: admin@uda.local", label_visibility="collapsed"
            )
            password = st.text_input(
                "Mot de passe", type="password", placeholder="••••••••••••", label_visibility="collapsed"
            )
            st.checkbox("Se rappeler de moi", key="remember_me")
            
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if submitted:
            if email and password:
                try:
                    result = _auth_ctrl.login(email, password, ip="127.0.0.1")
                    st.session_state.update({
                        "token": result["token"],
                        "user_id": result["user_id"],
                        "role": result["role"],
                        "nom": result["nom"],
                        "current_page": "dashboard",
                    })
                    st.success("Connexion réussie!")
                    st.rerun()
                except Exception:
                    st.error("Identifiants invalides")
            else:
                st.error("Veuillez remplir tous les champs")

        st.markdown(
            """
            <div class="auth-links">
                <a href="#">Mot de passe oublié ?</a>
                <a href="#">Questions ?</a>
            </div>
            <div class="auth-footer">Copyright © 2026 - Tous droits réservés</div>
            """,
            unsafe_allow_html=True,
        )
