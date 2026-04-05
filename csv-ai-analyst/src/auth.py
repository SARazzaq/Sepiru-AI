"""
Sepiru AI — Premium Authentication Gate.
Fully self-contained — no external CSS dependency.
"""

import os
import streamlit as st


def _get_password() -> str:
    try:
        p = st.secrets.get("APP_PASSWORD", "")
        if p:
            return p
    except Exception:
        pass
    return os.getenv("APP_PASSWORD", "sepiru")


def require_auth():
    if st.session_state.get("_auth"):
        return

    # ── Inject all styles inline — no external CSS needed ────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400;1,500&family=DM+Sans:wght@300;400;500&display=swap');

    /* Hide everything Streamlit */
    #MainMenu, footer, header,
    section[data-testid="stSidebar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] { display:none !important; }

    /* Full viewport dark background */
    html, body, .stApp {
        background:#020208 !important;
        margin:0 !important; padding:0 !important;
    }

    /* Aurora glow behind card */
    .stApp::before {
        content:'';
        position:fixed; inset:0;
        background:
            radial-gradient(ellipse 70% 50% at 50% 0%, rgba(201,168,76,.1) 0%, transparent 60%),
            radial-gradient(ellipse 40% 30% at 20% 80%, rgba(99,102,241,.06) 0%, transparent 55%),
            radial-gradient(ellipse 40% 30% at 80% 70%, rgba(16,185,129,.04) 0%, transparent 55%);
        pointer-events:none; z-index:0;
    }

    /* Push block container to fill viewport */
    .main .block-container {
        min-height:100vh !important;
        display:flex !important;
        flex-direction:column !important;
        align-items:center !important;
        justify-content:center !important;
        padding:2rem !important;
        max-width:100% !important;
        position:relative; z-index:1;
    }

    /* ── Login wrapper ── */
    .sep-login-outer {
        width:100%;
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        gap:0;
    }

    /* ── Hero text ── */
    .sep-hero {
        text-align:center;
        margin-bottom:3rem;
        animation:sepFadeUp 1s cubic-bezier(.22,1,.36,1) both;
    }
    .sep-name {
        font-family:'Playfair Display',serif;
        font-size:clamp(3.5rem,8vw,6rem);
        font-weight:500;
        font-style:italic;
        background:linear-gradient(135deg,#f5e080 0%,#e8c96a 30%,#c9a84c 60%,#f5e8b8 100%);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        background-clip:text;
        line-height:1.05;
        margin:0 0 1rem;
        filter:drop-shadow(0 0 40px rgba(201,168,76,.35));
        animation:sepFadeUp 1s cubic-bezier(.22,1,.36,1) .1s both,
                  sepGlow 4s ease-in-out 1.5s infinite;
    }
    .sep-tagline {
        font-family:'DM Sans',sans-serif;
        font-size:clamp(.85rem,2vw,1.05rem);
        font-weight:300;
        color:#8888aa;
        letter-spacing:.5px;
        line-height:1.6;
        max-width:480px;
        margin:0 auto;
        animation:sepFadeUp .9s cubic-bezier(.22,1,.36,1) .3s both;
    }
    .sep-tagline em {
        color:#c9a84c;
        font-style:normal;
    }

    /* ── Card ── */
    .sep-card {
        width:100%;
        max-width:400px;
        background:linear-gradient(160deg,rgba(12,12,32,.95) 0%,rgba(8,8,24,.98) 100%);
        border:1px solid rgba(201,168,76,.2);
        border-radius:24px;
        padding:2.5rem 2.5rem 2rem;
        position:relative;
        overflow:hidden;
        animation:sepFadeUp .9s cubic-bezier(.22,1,.36,1) .5s both;
        backdrop-filter:blur(20px);
    }
    .sep-card::before {
        content:'';
        position:absolute;top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,
            transparent,rgba(201,168,76,.2) 20%,
            rgba(248,230,140,.9) 50%,
            rgba(201,168,76,.2) 80%,transparent);
    }
    .sep-card::after {
        content:'';
        position:absolute;top:-60px;left:50%;transform:translateX(-50%);
        width:300px;height:150px;
        background:radial-gradient(ellipse,rgba(201,168,76,.08) 0%,transparent 65%);
        pointer-events:none;
    }
    .sep-card-label {
        font-family:'DM Sans',sans-serif;
        font-size:.6rem;font-weight:400;
        color:#4a4a6a;letter-spacing:3px;text-transform:uppercase;
        margin-bottom:.6rem;display:block;
    }

    /* ── Input override ── */
    .sep-card .stTextInput > div > div > input {
        background:rgba(255,255,255,.04) !important;
        border:1px solid rgba(201,168,76,.18) !important;
        border-radius:10px !important;
        color:#f0ede6 !important;
        font-family:'DM Sans',sans-serif !important;
        font-size:1rem !important;
        letter-spacing:5px !important;
        text-align:center !important;
        padding:.8rem 1rem !important;
        caret-color:#c9a84c !important;
        transition:all .25s ease !important;
    }
    .sep-card .stTextInput > div > div > input:focus {
        border-color:rgba(201,168,76,.5) !important;
        box-shadow:0 0 0 3px rgba(201,168,76,.08),
                   0 0 30px rgba(201,168,76,.06) !important;
        outline:none !important;
    }
    .sep-card .stTextInput > div > div > input::placeholder {
        color:#2a2a42 !important;
        letter-spacing:6px !important;
    }

    /* ── Button override ── */
    .sep-card .stButton > button {
        width:100% !important;
        background:linear-gradient(135deg,#c9a84c 0%,#e8c96a 50%,#c9a84c 100%) !important;
        background-size:200% auto !important;
        color:#020208 !important;
        border:none !important;
        border-radius:10px !important;
        font-family:'DM Sans',sans-serif !important;
        font-size:.7rem !important;
        font-weight:500 !important;
        letter-spacing:3px !important;
        text-transform:uppercase !important;
        padding:.8rem !important;
        margin-top:.8rem !important;
        box-shadow:0 4px 24px rgba(201,168,76,.25) !important;
        transition:all .3s ease !important;
        animation:goldShift 3s linear infinite !important;
    }
    .sep-card .stButton > button:hover {
        box-shadow:0 8px 40px rgba(201,168,76,.45) !important;
        transform:translateY(-2px) !important;
    }

    /* ── Error ── */
    .sep-error {
        margin-top:.8rem;
        padding:.6rem 1rem;
        background:rgba(244,63,94,.07);
        border:1px solid rgba(244,63,94,.18);
        border-radius:8px;
        font-family:'DM Sans',sans-serif;
        font-size:.78rem;color:#fda4af;
        text-align:center;
    }

    /* ── Footer ── */
    .sep-footer {
        margin-top:1.5rem;
        font-family:'DM Sans',sans-serif;
        font-size:.58rem;color:#2a2a42;
        letter-spacing:2px;text-transform:uppercase;
        text-align:center;
        animation:sepFadeUp .8s ease .8s both;
    }

    /* ── Keyframes ── */
    @keyframes sepFadeUp {
        from { opacity:0; transform:translateY(24px); filter:blur(6px); }
        to   { opacity:1; transform:translateY(0);    filter:blur(0); }
    }
    @keyframes sepGlow {
        0%,100% { filter:drop-shadow(0 0 20px rgba(201,168,76,.25)); }
        50%      { filter:drop-shadow(0 0 50px rgba(201,168,76,.55)); }
    }
    @keyframes goldShift {
        0%   { background-position:0% center; }
        100% { background-position:200% center; }
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero section ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="sep-login-outer">
        <div class="sep-hero">
            <div class="sep-name">Sepiru AI</div>
            <div class="sep-tagline">
                Most tools make you work for the answer.<br>
                <em>Sepiru AI just answers.</em>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Password card ─────────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="sep-card">', unsafe_allow_html=True)
        st.markdown('<span class="sep-card-label">Access Key</span>', unsafe_allow_html=True)

        pwd = st.text_input(
            label="pwd",
            type="password",
            placeholder="· · · · · · · ·",
            label_visibility="collapsed",
            key="_login_pwd"
        )

        enter = st.button("Enter →", use_container_width=True)

        if enter and pwd:
            if pwd == _get_password():
                st.session_state["_auth"] = True
                st.rerun()
            else:
                st.markdown(
                    '<div class="sep-error">Incorrect access key. Try again.</div>',
                    unsafe_allow_html=True
                )
        elif enter and not pwd:
            st.markdown(
                '<div class="sep-error">Please enter your access key.</div>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sep-footer">✦ Authorised access only</div>', unsafe_allow_html=True)

    st.stop()
