"""Utility functions for Streamlit custom styling and components."""

import streamlit as st

PRIMARY_COLOR = "#93DC5C"
BACKGROUND_COLOR = "#F8F9FA"
TEXT_COLOR = "#333333"

def inject_custom_css() -> None:
    """Inject custom CSS to overhaul the Streamlit UI."""
    css = f"""
    <!-- FontAwesome for professional icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        /* Global Text Visibility Fix */
        .main .block-container h1, .main .block-container h2, .main .block-container h3, .main .block-container p {{
            color: #2c3e50 !important;
            font-weight: 700 !important;
        }}
        
        .main .block-container {{
            color: #2c3e50 !important;
        }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: {PRIMARY_COLOR};
            color: white;
            padding-top: 0px;
        }}
        
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        
        /* Navigation Buttons in Sidebar */
        div.stButton > button {{
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
        
        div.stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white !important;
            transform: translateX(5px);
        }}
        
        /* Main Content Background */
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}

        /* Metric Cards */
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
            color: #1a1a1a !important;
            line-height: 1;
        }}
        
        .metric-label {{
            font-size: 15px;
            color: #64748b !important;
            font-weight: 600;
            margin-top: 4px;
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
        st.image("assets/logo.png", use_container_width=True)
    
    st.markdown(
        f"""
        <div style='text-align: center; padding: 10px 0;'>
            <h3 style='margin: 0; color: white !important;'>{nom}</h3>
            <p style='margin: 0; color: rgba(255,255,255,0.7) !important; font-size: 0.9em;'>{role.capitalize()}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
