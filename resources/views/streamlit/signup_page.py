"""Streamlit signup page."""

import streamlit as st

from app.Http.Controllers.auth_controller import AuthController

_auth_ctrl = AuthController()


# Re-use the exact same CSS as login for visual consistency
_AUTH_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #93DC5C 0%, #4e732d 100%) !important;
    font-family: 'Nunito', sans-serif !important;
}
[data-testid="stHeader"], [data-testid="stSidebar"],
.stDeployButton, [data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stMain"] {
    display: flex;
    justify-content: center;
    align-items: center;
}
.block-container {
    padding: 0 !important;
    max-width: 1000px !important;
    width: 100% !important;
    background: #ffffff;
    border-radius: 20px;
    box-shadow: 0 25px 60px rgba(0,0,0,0.30);
    overflow: hidden;
    margin-top: 5vh;
    margin-bottom: 5vh;
}
[data-testid="column"]:nth-of-type(1) {
    background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=2015&auto=format&fit=crop');
    background-size: cover;
    background-position: center;
    position: relative;
    min-height: 620px;
    padding: 0 !important;
    margin: 0 !important;
    border: 2px solid #2c3e50 !important;
    border-radius: 20px 0 0 20px !important;
    box-sizing: border-box !important;
}
[data-testid="column"]:nth-of-type(1)::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.28);
    border-radius: 18px 0 0 18px;
}
.auth-logo-wrapper {
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    min-height: 620px;
}
.auth-logo-box {
    background: rgba(147, 220, 92, 0.95);
    padding: 28px 34px;
    border-radius: 22px;
    text-align: center;
    box-shadow: 0 12px 35px rgba(0,0,0,0.3);
}
.auth-logo-box img { width: 85px; display: block; margin: 0 auto 8px; }
.auth-logo-box .brand { color: #fff; font-weight: 700; font-size: 1.25rem; letter-spacing: 1px; }
[data-testid="column"]:nth-of-type(2) {
    padding: 40px 60px 40px 20px !important;
    box-sizing: border-box !important;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.auth-form-title {
    font-family: 'Nunito', sans-serif;
    font-size: 1.6rem;
    font-weight: 400;
    color: #2c3e50 !important;
    text-align: center;
    margin-bottom: 24px;
    margin-top: 0;
}

/* Form Container */
[data-testid="stForm"] {
    background-color: #ffffff !important;
    border: 1px solid #eef0f3 !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08) !important;
    padding: 30px 25px !important;
    margin: 0 auto !important;
    max-width: 95% !important;
    box-sizing: border-box !important;
}

/* 5. Inputs */
div[data-baseweb="input"] {
    border-radius: 10rem !important;
    border: 1px solid #d1d3e2 !important;
    background-color: #f8f9fc !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.2s ease-in-out !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #93DC5C !important;
    box-shadow: 0 0 0 0.2rem rgba(147,220,92,0.25) !important;
}
.stTextInput input {
    font-size: 0.85rem !important;
    padding: 1.5rem 1rem !important;
    height: auto !important;
    font-family: 'Nunito', sans-serif !important;
    color: #93DC5C !important;
    font-weight: 600 !important;
    caret-color: #93DC5C !important;
    background-color: transparent !important;
}
.stTextInput input::placeholder {
    color: #b0b0b0 !important;
    opacity: 1 !important;
    font-weight: 400 !important;
}
[data-testid="stFormSubmitButton"] button {
    font-size: 0.85rem !important;
    border-radius: 10rem !important;
    padding: 0.75rem 1rem !important;
    height: auto !important;
    background: #93DC5C !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-family: 'Nunito', sans-serif !important;
    border: none !important;
    margin-top: 12px !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: #7ab84d !important;
    box-shadow: 0 4px 14px rgba(147,220,92,0.35) !important;
}
.auth-footer {
    text-align: center;
    color: #333 !important;
    font-size: 0.85rem;
    font-family: 'Nunito', sans-serif;
    margin-top: 22px;
    padding-bottom: 10px;
}
div.stButton button {
    background: transparent !important;
    color: #333 !important;
    border: none !important;
    border-top: 1px solid #eef0f3 !important;
    border-radius: 0 !important;
    padding: 14px 0 0 0 !important;
    margin-top: 14px !important;
    box-shadow: none !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    font-family: 'Nunito', sans-serif !important;
    width: 100% !important;
}
div.stButton button:hover {
    color: #93DC5C !important;
    text-decoration: underline !important;
}
@media (max-width: 1000px) {
    [data-testid="stHorizontalBlock"] { flex-direction: column; }
    [data-testid="column"]:nth-of-type(1) { display: none !important; }
    [data-testid="column"]:nth-of-type(2) { width: 100% !important; padding: 40px 30px !important; }
    .block-container { max-width: 480px !important; margin-top: 10vh; }
}
</style>
"""


def render() -> None:
    """Render the signup page with the green-themed split card."""

    # ── Font (separate call) ──────────────────────────────────────
    st.markdown(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&display=swap">',
        unsafe_allow_html=True,
    )

    # ── CSS (own call) ────────────────────────────────────────────
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)

    # ── Layout ────────────────────────────────────────────────────
    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown(
            """
            <div class="auth-logo-wrapper">
                <div class="auth-logo-box">
                    <img src="https://cdn-icons-png.flaticon.com/512/2103/2103633.png" alt="UDA">
                    <span class="brand">Bienvenue</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown('<p class="auth-form-title">Inscription</p>', unsafe_allow_html=True)

        with st.form("signup_form", clear_on_submit=False):
            nom = st.text_input("Nom complet", placeholder="Jean Dupont", label_visibility="collapsed")
            email = st.text_input("Email", placeholder="jean.dupont@example.com", label_visibility="collapsed")
            password = st.text_input("Mot de passe", type="password", placeholder="Mot de passe", label_visibility="collapsed")
            confirm_password = st.text_input("Confirmer", type="password", placeholder="Confirmer le mot de passe", label_visibility="collapsed")
            submitted = st.form_submit_button("S'inscrire", use_container_width=True)

        if submitted:
            if nom and email and password and confirm_password:
                if password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas")
                else:
                    try:
                        _auth_ctrl.register(nom, email, password, ip="127.0.0.1")
                        st.success("Compte cree avec succes!")
                        st.session_state["current_page"] = "login"
                        st.rerun()
                    except Exception:
                        st.error("Erreur lors de l'inscription")
            else:
                st.error("Veuillez remplir tous les champs")

        if st.button("Deja un compte ? Se connecter", key="goto_login", use_container_width=True):
            st.session_state["current_page"] = "login"
            st.rerun()

        st.markdown('<div class="auth-footer">Copyright &copy; 2026 - Tous droits reserves</div>', unsafe_allow_html=True)
