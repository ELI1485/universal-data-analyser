"""Streamlit login page."""

import streamlit as st

from app.Http.Controllers.auth_controller import AuthController

_auth_ctrl = AuthController()


def render() -> None:
    """Render the login page with the green-themed split card."""

    # ---------------------------------------------------------------
    # CSS
    # ---------------------------------------------------------------
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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

        /* The logo box (UDA Portal) — keep green branding */
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
            color: #ffffff;
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

        /* 4. Title — black */
        .auth-form-title {
            font-family: 'Nunito', sans-serif;
            font-size: 1.65rem;
            font-weight: 400;
            color: #000000 !important;
            text-align: center;
            margin-bottom: 30px;
            margin-top: 0;
        }

        /* 5. Form inputs:
              - typed text: green (#93DC5C)
              - placeholder: light visible gray
        */
        .stTextInput > div > div > input {
            font-size: 0.85rem !important;
            border-radius: 10rem !important;
            padding: 1.5rem 1rem !important;
            height: auto !important;
            border: 1px solid #d1d3e2 !important;
            background-color: #ffffff !important;
            font-family: 'Nunito', sans-serif !important;
            color: #93DC5C !important;
            font-weight: 600 !important;
            caret-color: #93DC5C !important;
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #93DC5C !important;
            box-shadow: 0 0 0 0.2rem rgba(147, 220, 92, 0.25) !important;
            color: #93DC5C !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #b8bcc4 !important;
            opacity: 1 !important;
            font-weight: 400 !important;
        }

        /* 6. Checkbox — black label */
        .stCheckbox { padding-left: 0.5rem; }
        .stCheckbox label { line-height: 1.5rem !important; font-family: 'Nunito', sans-serif !important; }
        .stCheckbox label span,
        .stCheckbox label p {
            font-size: 0.85rem !important;
            color: #000000 !important;
        }

        /* 7. Submit button — keep green */
        [data-testid="stFormSubmitButton"] > button {
            font-size: 0.85rem !important;
            border-radius: 10rem !important;
            padding: 0.75rem 1rem !important;
            height: auto !important;
            background-color: #93DC5C !important;
            color: #ffffff !important;
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

        /* 8. Links — black by default; the forgot-password link is green */
        .auth-links { text-align: center; margin-top: 18px; }
        .auth-links a {
            text-decoration: none;
            font-size: 0.85rem;
            font-family: 'Nunito', sans-serif;
            display: block;
            margin-bottom: 10px;
            color: #000000;
        }
        .auth-links a.forgot-link {
            color: #93DC5C !important;
            font-weight: 600;
        }
        .auth-links a.forgot-link:hover { color: #7ab84d !important; text-decoration: underline; }

        /* Signup link rendered as a Streamlit button styled as a text-link */
        [data-testid="stMain"] div[data-testid="stButton"][data-key="goto_signup"] > button,
        [data-testid="stMain"] div.stButton[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            color: #000000 !important;
            border: none !important;
            border-top: 1px solid #eef0f3 !important;
            border-radius: 0 !important;
            padding: 14px 0 0 0 !important;
            margin-top: 18px !important;
            box-shadow: none !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            font-family: 'Nunito', sans-serif !important;
            text-align: center !important;
            width: 100% !important;
            transition: color 0.15s ease !important;
        }
        [data-testid="stMain"] div[data-testid="stButton"][data-key="goto_signup"] > button:hover {
            color: #93DC5C !important;
            text-decoration: underline !important;
        }

        .auth-footer {
            text-align: center;
            color: #000000;
            font-size: 0.8rem;
            font-family: 'Nunito', sans-serif;
            margin-top: 22px;
        }

        /* 9. Responsive */
        @media (max-width: 1000px) {
            [data-testid="stHorizontalBlock"] { flex-direction: column; }
            [data-testid="column"]:nth-of-type(1) { display: none !important; }
            [data-testid="column"]:nth-of-type(2) { width: 100% !important; padding: 40px 30px !important; }
            .block-container { max-width: 500px !important; margin-top: 10vh; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------
    # Layout
    # ---------------------------------------------------------------
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
                "Mot de passe", type="password", placeholder="Mot de passe", label_visibility="collapsed"
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
                    st.success("Connexion reussie!")
                    st.rerun()
                except Exception:
                    st.error("Identifiants invalides")
            else:
                st.error("Veuillez remplir tous les champs")

        # Forgot-password link directly under the submit button (green).
        # Sign-up link at the very bottom.
        # The "Questions ?" link has been removed.
        st.markdown(
            """
            <div class="auth-links">
                <a href="#" class="forgot-link">Mot de passe oublie ?</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Streamlit-native button used as the bottom signup link
        # (styled as a text link via CSS). This is functional whereas a plain
        # HTML <a> cannot mutate Streamlit's session_state.
        if st.button(
            "Don't have an account? Create an acc",
            key="goto_signup",
            use_container_width=True,
        ):
            st.session_state["current_page"] = "signup"
            st.rerun()

        st.markdown(
            '<div class="auth-footer">Copyright &copy; 2026 - Tous droits reserves</div>',
            unsafe_allow_html=True,
        )
