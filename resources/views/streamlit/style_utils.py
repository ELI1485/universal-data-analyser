"""Utility functions for Streamlit custom styling and components."""

import streamlit as st

PRIMARY_COLOR = "#93DC5C"
PRIMARY_DARK = "#4e732d"
BACKGROUND_COLOR = "#F8F9FA"
TEXT_COLOR = "#1a1a1a"
TEXT_MUTED = "#475569"


def inject_custom_css() -> None:
    """Inject the global Streamlit theme.

    Strategy:
    - Force dark text in the main content area (fixes the "white-on-white"
      visibility bug). The selectors are scoped to ``[data-testid="stMain"]``
      so the sidebar (white text on green) is untouched.
    - Sidebar stays white-on-green.
    - Login/signup pages inject their own CSS later in the page lifecycle,
      so their input colours and gradients still take precedence.
    """
    css = f"""
    <!-- FontAwesome (used everywhere instead of emojis) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        /* =====================================================
         * 1. GLOBAL TEXT VISIBILITY FIX
         *    Force dark text across the main content area so it
         *    is readable on the light background.
         * ===================================================== */
        [data-testid="stMain"],
        [data-testid="stMain"] [data-testid="stMarkdownContainer"],
        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4,
        [data-testid="stMain"] h5,
        [data-testid="stMain"] h6,
        [data-testid="stMain"] p,
        [data-testid="stMain"] li,
        [data-testid="stMain"] label,
        [data-testid="stMain"] span,
        [data-testid="stMain"] caption,
        [data-testid="stMain"] [data-testid="stCaptionContainer"],
        [data-testid="stMain"] [data-testid="stMetricLabel"],
        [data-testid="stMain"] [data-testid="stMetricValue"],
        [data-testid="stMain"] [data-testid="stMetricDelta"],
        [data-testid="stMain"] [data-testid="stTable"] td,
        [data-testid="stMain"] [data-testid="stTable"] th,
        [data-testid="stMain"] [data-testid="stDataFrame"] td,
        [data-testid="stMain"] [data-testid="stDataFrame"] th,
        [data-testid="stMain"] .stTabs [data-baseweb="tab"] {{
            color: {TEXT_COLOR} !important;
        }}

        [data-testid="stMain"] h1,
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4 {{
            font-weight: 700 !important;
        }}

        /* Inputs in the main area — readable */
        [data-testid="stMain"] input,
        [data-testid="stMain"] textarea,
        [data-testid="stMain"] select {{
            color: {TEXT_COLOR} !important;
        }}

        /* The metric-card label is muted on purpose */
        [data-testid="stMain"] .metric-card .metric-label {{
            color: {TEXT_MUTED} !important;
        }}

        /* Status messages: keep their semantic colours */
        [data-testid="stMain"] [data-testid="stAlert"] p,
        [data-testid="stMain"] [data-testid="stAlert"] div {{
            color: inherit !important;
        }}

        /* =====================================================
         * 2. APP BACKGROUND
         * ===================================================== */
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}

        /* =====================================================
         * 3. SIDEBAR (white on green)
         * ===================================================== */
        [data-testid="stSidebar"] {{
            background-color: {PRIMARY_COLOR};
            color: white;
            padding-top: 0px;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: rgba(255, 255, 255, 0.25) !important;
        }}

        /* Sidebar nav buttons */
        [data-testid="stSidebar"] div.stButton > button {{
            background-color: transparent;
            color: white !important;
            border: 1px solid transparent;
            border-radius: 8px;
            text-align: left;
            padding: 12px 20px;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
            width: 100%;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        [data-testid="stSidebar"] div.stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white !important;
            transform: translateX(5px);
        }}

        /* =====================================================
         * 4. MAIN CONTENT BUTTONS (light primary)
         *    Sidebar override above wins for sidebar buttons.
         * ===================================================== */
        [data-testid="stMain"] div.stButton > button {{
            background-color: {PRIMARY_COLOR};
            color: #ffffff !important;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        [data-testid="stMain"] div.stButton > button:hover {{
            background-color: {PRIMARY_DARK};
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(147, 220, 92, 0.35);
        }}

        /* =====================================================
         * 5. METRIC CARDS
         * ===================================================== */
        .metric-card {{
            background-color: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 25px;
            border-left: 6px solid {PRIMARY_COLOR};
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        .metric-icon {{
            background-color: {PRIMARY_COLOR}15;
            color: {PRIMARY_COLOR} !important;
            font-size: 28px;
            width: 60px;
            height: 60px;
            display: flex;
            justify-content: center;
            align-items: center;
            border-radius: 12px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: 800;
            color: {TEXT_COLOR} !important;
            line-height: 1;
        }}
        .metric-label {{
            font-size: 15px;
            color: {TEXT_MUTED} !important;
            font-weight: 600;
            margin-top: 4px;
        }}

        /* =====================================================
         * 6. PAGE HEADER ICONS (FontAwesome)
         * ===================================================== */
        [data-testid="stMain"] h2 i.fa-solid,
        [data-testid="stMain"] h3 i.fa-solid,
        [data-testid="stMain"] h4 i.fa-solid {{
            color: {PRIMARY_COLOR} !important;
            margin-right: 6px;
        }}

        /* =====================================================
         * 7. TABS
         * ===================================================== */
        [data-testid="stMain"] .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
        }}
        [data-testid="stMain"] .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: {PRIMARY_DARK} !important;
            border-bottom-color: {PRIMARY_COLOR} !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, fa_icon: str) -> None:
    """Render a custom premium metric card using FontAwesome.

    Args:
        label: The label of the metric.
        value: The value string.
        fa_icon: FontAwesome class (e.g., 'fa-solid fa-users').
    """
    html = f"""
    <div class="metric-card">
        <div class="metric-icon"><i class="{fa_icon}"></i></div>
        <div class="metric-content">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar_header(nom: str, role: str) -> None:
    """Render the sidebar header with logo and user info."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("assets/logo.png", use_container_width=True)
        except Exception:
            # Logo file missing — degrade gracefully without crashing.
            st.markdown(
                "<div style='text-align:center; font-size: 28px; color:white;'>"
                "<i class='fa-solid fa-chart-pie'></i></div>",
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div style='text-align: center; padding: 10px 0;'>
            <h3 style='margin: 0; color: white !important;'>{nom}</h3>
            <p style='margin: 0; color: rgba(255,255,255,0.7) !important; font-size: 0.9em;'>{role.capitalize()}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.2);'>",
        unsafe_allow_html=True,
    )
