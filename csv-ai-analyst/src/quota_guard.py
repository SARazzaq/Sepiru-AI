"""
Quota Guard — Multi-API daily quota tracking with maintenance mode.
Tracks Groq + Gemini usage in session state (no file I/O — works on Streamlit Cloud).
Shows maintenance page when any critical API is exhausted.

Free tier limits:
  Groq:   14,400 req/day  → stop at 14,000 (400 buffer)
  Gemini: 1,500  req/day  → stop at 1,400  (100 buffer)
"""

from datetime import datetime, timezone, timedelta

# ── Limits ────────────────────────────────────────────────────────────────────
LIMITS = {
    "groq":   {"daily": 14000, "label": "Groq (LLaMA 3.3 70B)"},
    "gemini": {"daily": 1400,  "label": "Gemini 2.0 Flash"},
}


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _get_state(api: str) -> dict:
    """Get or initialise quota state for an API in session state."""
    try:
        import streamlit as st
        key = f"_quota_{api}"
        if key not in st.session_state or \
           st.session_state[key].get("date") != _today_utc():
            st.session_state[key] = {"date": _today_utc(), "count": 0}
        return st.session_state[key]
    except Exception:
        return {"date": _today_utc(), "count": 0}


def get_usage(api: str = "groq") -> dict:
    """Returns usage stats for a given API."""
    d     = _get_state(api)
    limit = LIMITS.get(api, {}).get("daily", 14000)
    remaining = max(0, limit - d["count"])
    return {
        "api":       api,
        "date":      d["date"],
        "count":     d["count"],
        "remaining": remaining,
        "limit":     limit,
        "pct_used":  round(d["count"] / limit * 100, 1) if limit else 0,
        "exhausted": remaining == 0,
        "label":     LIMITS.get(api, {}).get("label", api),
    }


def increment(api: str = "groq", n: int = 1):
    """Increment usage counter for an API after a successful call."""
    try:
        import streamlit as st
        key = f"_quota_{api}"
        d   = _get_state(api)
        d["count"] = d.get("count", 0) + n
        st.session_state[key] = d
    except Exception:
        pass


def can_proceed(api: str = "groq") -> bool:
    """Returns False when daily quota for an API is exhausted."""
    return get_usage(api)["remaining"] > 0


def reset_time_utc() -> str:
    """Human-readable time until quota resets (midnight UTC)."""
    now          = datetime.now(timezone.utc)
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    delta = next_midnight - now
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m = rem // 60
    return f"{h}h {m}m"


def check_all_quotas() -> dict:
    """
    Check all APIs. Returns:
    {
      "ok": bool,           # True if all critical APIs have quota
      "exhausted": [str],   # list of exhausted API names
      "warnings": [str],    # APIs below 10% remaining
    }
    """
    exhausted = []
    warnings  = []
    for api in LIMITS:
        u = get_usage(api)
        if u["exhausted"]:
            exhausted.append(u["label"])
        elif u["pct_used"] >= 90:
            warnings.append(f"{u['label']} ({u['remaining']} req left)")
    return {
        "ok":        len(exhausted) == 0,
        "exhausted": exhausted,
        "warnings":  warnings,
    }


def maintenance_gate():
    """
    Call this in app.py after auth.
    Shows a premium maintenance page if any critical API quota is exhausted.
    Blocks the app until quota resets.
    """
    status = check_all_quotas()
    if status["ok"]:
        return  # all good

    import streamlit as st

    st.markdown("""
    <style>
    #MainMenu,footer,header,section[data-testid="stSidebar"],
    [data-testid="stToolbar"]{display:none!important;}
    html,body{margin:0!important;padding:0!important;}
    .stApp{background:#020208!important;}
    .main .block-container{
        min-height:100vh!important;display:flex!important;
        flex-direction:column!important;align-items:center!important;
        justify-content:center!important;padding:2rem!important;
    }
    </style>
    """, unsafe_allow_html=True)

    exhausted_str = " &amp; ".join(status["exhausted"])
    resets_in     = reset_time_utc()

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,300&family=Space+Grotesk:wght@300;400;500&display=swap');
    @keyframes mPulse{{0%,100%{{opacity:.6;}}50%{{opacity:1;}}}}
    @keyframes mFade{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}}
    </style>
    <div style="max-width:480px;margin:auto;text-align:center;
         animation:mFade .8s ease both;">

        <!-- Gear icon -->
        <div style="font-size:3.5rem;margin-bottom:1.2rem;
             animation:mPulse 2.5s ease-in-out infinite;">⚙️</div>

        <!-- Title -->
        <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
             font-size:2.4rem;font-weight:300;
             background:linear-gradient(135deg,#f5e080,#c9a84c);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;
             background-clip:text;margin-bottom:.6rem;">
            Under Maintenance
        </div>

        <!-- Subtitle -->
        <div style="font-family:'Space Grotesk',sans-serif;font-size:.88rem;
             font-weight:300;color:rgba(255,255,255,.4);line-height:1.7;
             margin-bottom:1.8rem;">
            Daily AI quota has been reached to keep this service free.<br>
            Sepiru AI will automatically resume when quota resets.
        </div>

        <!-- Info card -->
        <div style="background:rgba(201,168,76,.06);
             border:1px solid rgba(201,168,76,.18);border-radius:16px;
             padding:1.5rem;margin-bottom:1.2rem;">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:.58rem;
                 font-weight:500;letter-spacing:3px;text-transform:uppercase;
                 color:rgba(201,168,76,.4);margin-bottom:.6rem;">
                Quota reached
            </div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:.88rem;
                 color:rgba(255,255,255,.5);margin-bottom:1rem;">
                {exhausted_str}
            </div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:.58rem;
                 font-weight:500;letter-spacing:3px;text-transform:uppercase;
                 color:rgba(201,168,76,.4);margin-bottom:.4rem;">
                Resets in
            </div>
            <div style="font-family:'Cormorant Garamond',serif;font-style:italic;
                 font-size:2.2rem;font-weight:300;
                 background:linear-gradient(135deg,#f5e080,#c9a84c);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;">
                {resets_in}
            </div>
        </div>

        <div style="font-family:'Space Grotesk',sans-serif;font-size:.55rem;
             color:rgba(255,255,255,.1);letter-spacing:2px;text-transform:uppercase;">
            ✦ Powered by free AI APIs &nbsp;·&nbsp; Sepiru AI
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()
