"""
Sepiru AI — Authentication gate.
Password stored in st.secrets (cloud) or APP_PASSWORD env var (local).
"""

import os
import streamlit as st
import streamlit.components.v1 as components


def _get_password() -> str:
    """Read password from st.secrets or env. Falls back to 'sepiru' for dev."""
    try:
        p = st.secrets.get("APP_PASSWORD", "")
        if p:
            return p
    except Exception:
        pass
    return os.getenv("APP_PASSWORD", "sepiru")


def _login_page():
    """Render the premium cinematic login screen."""

    # Inject login-specific styles
    st.markdown("""
    <style>
    /* Hide all Streamlit chrome on login page */
    #MainMenu, footer, header,
    section[data-testid="stSidebar"],
    [data-testid="stToolbar"] { display:none !important; }

    .main .block-container {
        max-width:480px !important;
        padding:0 !important;
        margin:0 auto !important;
    }

    /* Login card */
    .login-wrap {
        min-height:100vh;
        display:flex;
        align-items:center;
        justify-content:center;
        padding:2rem;
    }
    .login-card {
        width:100%;
        max-width:420px;
        background:linear-gradient(160deg,#0c0c20 0%,#080818 100%);
        border:1px solid rgba(201,168,76,.18);
        border-radius:28px;
        padding:3.5rem 3rem 3rem;
        text-align:center;
        position:relative;
        overflow:hidden;
    }
    .login-card::before {
        content:'';
        position:absolute;top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,
            transparent,rgba(201,168,76,.2) 20%,
            rgba(248,230,140,1) 50%,
            rgba(201,168,76,.2) 80%,transparent);
    }
    .login-card::after {
        content:'';
        position:absolute;top:-80px;left:50%;transform:translateX(-50%);
        width:400px;height:200px;
        background:radial-gradient(ellipse,rgba(201,168,76,.1) 0%,transparent 65%);
        pointer-events:none;
    }
    .login-logo {
        font-family:'Playfair Display',serif;
        font-size:2.4rem;font-weight:500;font-style:italic;
        background:linear-gradient(135deg,#f5e080 0%,#e8c96a 35%,#c9a84c 70%,#f5e8b8 100%);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        background-clip:text;
        margin-bottom:.4rem;
        filter:drop-shadow(0 0 16px rgba(201,168,76,.4));
    }
    .login-tagline {
        font-family:'DM Sans',sans-serif;
        font-size:.68rem;font-weight:400;
        color:#4a4a6a;letter-spacing:3px;text-transform:uppercase;
        margin-bottom:2.8rem;
    }
    .login-label {
        font-family:'DM Sans',sans-serif;
        font-size:.62rem;font-weight:400;
        color:#4a4a6a;letter-spacing:2.5px;text-transform:uppercase;
        text-align:left;margin-bottom:.5rem;display:block;
    }

    /* Override Streamlit input inside login */
    .login-card .stTextInput > div > div > input {
        background:rgba(255,255,255,.04) !important;
        border:1px solid rgba(201,168,76,.2) !important;
        border-radius:10px !important;
        color:#f0ede6 !important;
        font-family:'DM Sans',sans-serif !important;
        font-size:.95rem !important;
        padding:.75rem 1rem !important;
        text-align:center !important;
        letter-spacing:4px !important;
        caret-color:#c9a84c !important;
        transition:all .25s ease !important;
    }
    .login-card .stTextInput > div > div > input:focus {
        border-color:rgba(201,168,76,.55) !important;
        box-shadow:0 0 0 3px rgba(201,168,76,.08),
                   0 0 40px rgba(201,168,76,.06) !important;
        outline:none !important;
    }
    .login-card .stButton > button {
        width:100% !important;
        background:linear-gradient(135deg,#c9a84c 0%,#e8c96a 50%,#c9a84c 100%) !important;
        background-size:200% auto !important;
        color:#020208 !important;
        border:none !important;
        border-radius:10px !important;
        font-family:'DM Sans',sans-serif !important;
        font-size:.72rem !important;
        font-weight:500 !important;
        letter-spacing:2.5px !important;
        text-transform:uppercase !important;
        padding:.75rem !important;
        margin-top:1.2rem !important;
        transition:all .3s ease !important;
        box-shadow:0 4px 20px rgba(201,168,76,.25) !important;
    }
    .login-card .stButton > button:hover {
        box-shadow:0 8px 35px rgba(201,168,76,.45) !important;
        transform:translateY(-2px) !important;
    }
    .login-error {
        margin-top:1rem;
        padding:.65rem 1rem;
        background:rgba(244,63,94,.08);
        border:1px solid rgba(244,63,94,.2);
        border-radius:8px;
        font-family:'DM Sans',sans-serif;
        font-size:.78rem;color:#fda4af;
        letter-spacing:.3px;
    }
    .login-footer {
        margin-top:2rem;
        font-family:'DM Sans',sans-serif;
        font-size:.6rem;color:#2a2a42;
        letter-spacing:1.5px;text-transform:uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrap"><div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">Sepiru AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-tagline">Data Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<span class="login-label">Access Key</span>', unsafe_allow_html=True)

    pwd = st.text_input(
        label="password",
        type="password",
        placeholder="· · · · · · · ·",
        label_visibility="collapsed",
        key="_login_pwd"
    )

    enter = st.button("Enter", use_container_width=True)

    if enter or (pwd and pwd != ""):
        if pwd == _get_password():
            st.session_state["_auth"] = True
            st.rerun()
        elif pwd:
            st.markdown(
                '<div class="login-error">Incorrect access key. Try again.</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="login-footer">✦ Authorised access only</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)


def require_auth():
    """
    Call this at the top of app.py (after set_page_config).
    Blocks rendering until the correct password is entered.
    """
    if st.session_state.get("_auth"):
        return  # already authenticated

    _login_page()
    st.stop()
