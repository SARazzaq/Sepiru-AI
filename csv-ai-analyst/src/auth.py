"""
Sepiru AI — Security Gate.
- Math CAPTCHA (custom, no third-party)
- Honeypot bot trap
- No password required (public access)
- Rate limiting: max 30 attempts per session
- Input sanitisation
- All free, lifetime.
"""
import os
import re
import random
import time
import streamlit as st


def _new_captcha():
    ops = ['+', '-', 'x']
    op  = random.choice(ops)
    if op == '+':
        a, b = random.randint(10, 49), random.randint(10, 49)
        ans  = a + b
    elif op == '-':
        a, b = random.randint(20, 60), random.randint(5, 19)
        ans  = a - b
    else:
        a, b = random.randint(2, 12), random.randint(2, 12)
        ans  = a * b
    st.session_state["_cap_q"]   = f"{a} {op} {b}"
    st.session_state["_cap_ans"] = ans
    st.session_state["_cap_ts"]  = time.time()
    st.session_state["_cap_tries"] = st.session_state.get("_cap_tries", 0)


def require_auth():
    if st.session_state.get("_auth"):
        return

    # Block after 10 failed attempts (anti-brute-force)
    tries = st.session_state.get("_cap_tries", 0)
    if tries >= 10:
        st.markdown("""
        <style>
        #MainMenu,footer,header,section[data-testid="stSidebar"],
        [data-testid="stToolbar"]{display:none!important;}
        html,body{margin:0!important;padding:0!important;}
        .stApp{background:#000!important;}
        .main .block-container{
            min-height:100vh!important;display:flex!important;
            align-items:center!important;justify-content:center!important;
            padding:2rem!important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;max-width:420px;margin:auto;
        background:rgba(244,63,94,.07);border:1px solid rgba(244,63,94,.2);
        border-radius:20px;padding:3rem 2rem;">
            <div style="font-size:2.5rem;margin-bottom:1rem;">🚫</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;
            color:#fda4af;font-weight:500;margin-bottom:.8rem;">Too many failed attempts</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:.82rem;
            color:rgba(255,255,255,.3);">Please refresh the page to try again.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Generate captcha on first load or expiry (5 min)
    if "_cap_q" not in st.session_state or \
       time.time() - st.session_state.get("_cap_ts", 0) > 300:
        _new_captcha()

    q   = st.session_state["_cap_q"]
    ans = st.session_state["_cap_ans"]

    # ── Styles ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&family=Cormorant+Garamond:ital,wght@0,300;1,300;1,400&display=swap');

    #MainMenu,footer,header,
    [data-testid="stToolbar"],[data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    section[data-testid="stSidebar"]{{display:none!important;}}

    html,body{{margin:0!important;padding:0!important;overflow-x:hidden!important;}}
    .stApp{{background:#000!important;}}
    .main .block-container{{
        padding:1rem!important;max-width:100%!important;
        min-height:100vh!important;
        display:flex!important;flex-direction:column!important;
        align-items:center!important;justify-content:center!important;
    }}

    .sep-hero{{text-align:center;position:relative;z-index:10;
        padding:0 1rem;margin-bottom:.8rem;animation:sfadeUp .9s ease both;}}
    .sep-eyebrow{{font-family:'Space Grotesk',sans-serif;font-size:.6rem;
        font-weight:500;letter-spacing:5px;text-transform:uppercase;
        color:rgba(201,168,76,.5);margin-bottom:.7rem;}}
    .sep-name{{font-family:'Cormorant Garamond',serif;
        font-size:clamp(3rem,8vw,5.5rem);font-weight:300;font-style:italic;
        line-height:.95;
        background:linear-gradient(135deg,#fff 0%,#f5e080 25%,#c9a84c 55%,#f5e8b8 80%,#fff 100%);
        background-size:200% auto;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 40px rgba(201,168,76,.3));margin-bottom:.7rem;
        animation:sfadeUp .9s ease .05s both,sgoldFlow 4s linear 1s infinite;}}
    .sep-tagline{{font-family:'Space Grotesk',sans-serif;
        font-size:clamp(.78rem,1.8vw,.9rem);font-weight:300;
        color:rgba(255,255,255,.38);line-height:1.65;margin-bottom:.3rem;}}
    .sep-accent{{color:rgba(201,168,76,.8);font-weight:500;}}
    .sep-divider{{width:40px;height:1px;
        background:linear-gradient(90deg,transparent,rgba(201,168,76,.5),transparent);
        margin:.5rem auto .8rem;}}

    .sep-card{{background:linear-gradient(160deg,rgba(12,12,32,.97) 0%,rgba(8,8,24,.99) 100%);
        border:1px solid rgba(201,168,76,.18);border-radius:20px;
        padding:1.8rem 1.8rem 1.5rem;position:relative;overflow:hidden;
        animation:sfadeUp .8s ease .25s both;backdrop-filter:blur(20px);margin-bottom:.5rem;}}
    .sep-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,transparent,rgba(201,168,76,.2) 20%,
            rgba(248,230,140,.8) 50%,rgba(201,168,76,.2) 80%,transparent);}}

    .sep-math{{background:rgba(201,168,76,.05);border:1px solid rgba(201,168,76,.14);
        border-radius:12px;padding:1rem;text-align:center;margin:.5rem 0 .8rem;}}
    .sep-math-lbl{{font-size:.55rem;font-weight:500;letter-spacing:3px;text-transform:uppercase;
        color:rgba(201,168,76,.35);margin-bottom:.4rem;font-family:'Space Grotesk',sans-serif;}}
    .sep-math-eq{{font-family:'Cormorant Garamond',serif;font-size:2.4rem;
        font-weight:400;font-style:italic;
        background:linear-gradient(135deg,#f5e080,#c9a84c);background-size:200% auto;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 16px rgba(201,168,76,.35));line-height:1;margin-bottom:.3rem;
        animation:sgoldFlow 3s linear infinite;}}
    .sep-math-hint{{font-size:.58rem;color:rgba(255,255,255,.18);letter-spacing:.5px;
        font-family:'Space Grotesk',sans-serif;}}
    .sep-tries{{font-size:.58rem;color:rgba(255,255,255,.15);letter-spacing:1px;
        text-align:center;margin-top:.4rem;font-family:'Space Grotesk',sans-serif;}}

    .stTextInput>div>div>input{{background:rgba(255,255,255,.04)!important;
        border:1px solid rgba(201,168,76,.22)!important;border-radius:10px!important;
        color:#fff!important;font-family:'Space Grotesk',sans-serif!important;
        font-size:.95rem!important;letter-spacing:4px!important;text-align:center!important;
        padding:.7rem 1rem!important;caret-color:#c9a84c!important;transition:all .3s ease!important;}}
    .stTextInput>div>div>input:focus{{border-color:rgba(201,168,76,.55)!important;
        box-shadow:0 0 0 3px rgba(201,168,76,.08)!important;outline:none!important;}}
    .stTextInput>div>div>input::placeholder{{color:rgba(255,255,255,.1)!important;letter-spacing:5px!important;}}

    .stButton>button{{background:linear-gradient(135deg,#c9a84c 0%,#f5e080 50%,#c9a84c 100%)!important;
        background-size:200% auto!important;color:#000!important;border:none!important;
        border-radius:10px!important;font-family:'Space Grotesk',sans-serif!important;
        font-size:.68rem!important;font-weight:600!important;letter-spacing:3px!important;
        text-transform:uppercase!important;padding:.75rem!important;margin-top:.3rem!important;
        box-shadow:0 4px 24px rgba(201,168,76,.22)!important;transition:all .3s ease!important;
        animation:sgoldFlow 3s linear infinite!important;}}
    .stButton>button:hover{{box-shadow:0 8px 40px rgba(201,168,76,.45)!important;
        transform:translateY(-2px)!important;}}

    .sep-err{{text-align:center;font-family:'Space Grotesk',sans-serif;
        font-size:.75rem;color:#f87171;margin-top:.5rem;padding:.5rem .8rem;
        background:rgba(244,63,94,.07);border:1px solid rgba(244,63,94,.15);
        border-radius:8px;animation:sfadeUp .3s ease both;}}
    .sep-footer{{font-family:'Space Grotesk',sans-serif;font-size:.52rem;
        color:rgba(255,255,255,.1);letter-spacing:2px;text-transform:uppercase;
        text-align:center;margin-top:.6rem;}}

    @keyframes sfadeUp{{from{{opacity:0;transform:translateY(18px);filter:blur(4px);}}
        to{{opacity:1;transform:translateY(0);filter:blur(0);}}}}
    @keyframes sgoldFlow{{0%{{background-position:0% center;}}100%{{background-position:200% center;}}}}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(_canvas(), unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="sep-hero">
        <div class="sep-eyebrow">Data Intelligence Platform</div>
        <div class="sep-name">Sepiru AI</div>
        <div class="sep-tagline">Most tools make you work for the answer.
        <span class="sep-accent">Sepiru AI just answers.</span></div>
        <div class="sep-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown('<div class="sep-card">', unsafe_allow_html=True)

        # Math CAPTCHA display
        st.markdown(f"""
        <div class="sep-math">
            <div class="sep-math-lbl">Verify you're human</div>
            <div class="sep-math-eq">{q} = ?</div>
            <div class="sep-math-hint">Enter the answer below</div>
        </div>
        """, unsafe_allow_html=True)

        # Answer input
        cap = st.text_input("ans", placeholder="Answer",
                            label_visibility="collapsed", key="_cap")

        # Honeypot — rendered after answer, hidden by CSS
        hp = st.text_input("_hp", value="",
                           label_visibility="collapsed", key="_hp")

        c1, c2 = st.columns(2)
        with c1:
            btn = st.button("Enter →", use_container_width=True,
                            type="primary", key="_submit")
        with c2:
            if st.button("New ↺", use_container_width=True, key="_refresh"):
                _new_captcha()
                st.rerun()

        remaining = 10 - tries
        st.markdown(
            f'<div class="sep-tries">{remaining} attempt(s) remaining</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Validation ────────────────────────────────────────────────────────────
    if btn:
        error = None

        # 1. Honeypot — bot filled it
        if hp:
            error = "🤖 Automated access detected."

        # 2. Empty answer
        elif not cap:
            error = "Please solve the math problem."

        # 3. Non-numeric input (injection attempt)
        elif not re.match(r'^-?\d+$', cap.strip()):
            error = "Please enter a valid number."

        # 4. Math check
        else:
            try:
                given = int(cap.strip())
            except ValueError:
                given = None
            if given != ans:
                st.session_state["_cap_tries"] = tries + 1
                _new_captcha()
                error = f"✕ Wrong answer. New problem generated. ({10 - tries - 1} attempts left)"
            else:
                st.session_state["_auth"]      = True
                st.session_state["_cap_tries"] = 0
                st.rerun()

        if error:
            _, ec, _ = st.columns([1, 1.5, 1])
            with ec:
                st.markdown(f'<div class="sep-err">{error}</div>',
                            unsafe_allow_html=True)

    st.markdown(
        '<div class="sep-footer">✦ Protected by custom CAPTCHA &nbsp;·&nbsp; Sepiru AI</div>',
        unsafe_allow_html=True
    )
    st.stop()


def _canvas() -> str:
    return """
    <canvas id="_sep_cv" style="position:fixed;inset:0;width:100vw;height:100vh;
    pointer-events:none;z-index:0;"></canvas>
    <script>
    (function(){
        const cv=document.getElementById('_sep_cv');
        if(!cv)return;
        const cx=cv.getContext('2d');
        let W,H,pts,mx=9999,my=9999;
        function resize(){W=cv.width=window.innerWidth;H=cv.height=window.innerHeight;}
        resize();window.addEventListener('resize',resize);
        document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY;});
        const BLOBS=[
            {x:.5,y:-.05,rx:.85,ry:.5,h:42,s:80,a:.13,sp:.0002,ph:0},
            {x:.08,y:.9,rx:.5,ry:.35,h:258,s:70,a:.07,sp:.0003,ph:2.1},
            {x:.92,y:.8,rx:.45,ry:.3,h:162,s:65,a:.06,sp:.0004,ph:4.2},
        ];
        function initPts(){
            const N=Math.floor(W*H/18000);
            pts=Array.from({length:N},()=>({
                x:Math.random()*W,y:Math.random()*H,
                vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,
                r:Math.random()*1.4+.3,ph:Math.random()*Math.PI*2,
                spd:.01+Math.random()*.016,
            }));
        }
        initPts();window.addEventListener('resize',initPts);
        let t=0;
        function draw(){
            requestAnimationFrame(draw);cx.clearRect(0,0,W,H);t+=.007;
            BLOBS.forEach(b=>{
                const ox=Math.sin(t*b.sp*1000+b.ph)*.06;
                const oy=Math.cos(t*b.sp*800+b.ph)*.04;
                const px=(b.x+ox)*W,py=(b.y+oy)*H;
                const a=b.a*(.6+Math.sin(t+b.ph)*.4);
                const g=cx.createRadialGradient(px,py,0,px,py,Math.max(W,H)*b.rx);
                g.addColorStop(0,`hsla(${b.h},${b.s}%,60%,${a})`);
                g.addColorStop(.5,`hsla(${b.h},${b.s}%,40%,${a*.4})`);
                g.addColorStop(1,'transparent');
                cx.fillStyle=g;cx.fillRect(0,0,W,H);
            });
            for(let i=0;i<pts.length;i++){
                const a=pts[i];
                for(let j=i+1;j<pts.length;j++){
                    const b=pts[j];
                    const dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy;
                    if(d2<110*110){
                        cx.beginPath();
                        cx.strokeStyle=`rgba(201,168,76,${.08*(1-Math.sqrt(d2)/110)})`;
                        cx.lineWidth=.3;cx.moveTo(a.x,a.y);cx.lineTo(b.x,b.y);cx.stroke();
                    }
                }
            }
            for(const p of pts){
                p.ph+=p.spd;
                const g=.38+Math.sin(p.ph)*.25;
                const dx=p.x-mx,dy=p.y-my,d2=dx*dx+dy*dy;
                if(d2<8100){const d=Math.sqrt(d2);const f=(90-d)/90*.35;p.vx+=dx/d*f;p.vy+=dy/d*f;}
                p.vx*=.992;p.vy*=.992;
                cx.beginPath();cx.arc(p.x,p.y,p.r,0,Math.PI*2);
                cx.fillStyle=`rgba(201,168,76,${g})`;cx.fill();
                p.x+=p.vx;p.y+=p.vy;
                if(p.x<-10)p.x=W+10;if(p.x>W+10)p.x=-10;
                if(p.y<-10)p.y=H+10;if(p.y>H+10)p.y=-10;
            }
        }
        draw();
    })();
    </script>
    """


# ── Input sanitisation helpers (used by app.py) ───────────────────────────────
import re as _re

def sanitise_input(text: str, max_len: int = 2000) -> tuple[str, bool]:
    """
    Strip prompt injection attempts and dangerous patterns.
    Returns (cleaned_text, was_flagged).
    """
    if not text:
        return "", False

    # Truncate
    text = text[:max_len]

    # Detect injection patterns
    injection_patterns = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+",
        r"act\s+as\s+",
        r"jailbreak",
        r"dan\s+mode",
        r"system\s*prompt",
        r"<\s*script",
        r"javascript\s*:",
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__",
        r"os\.system",
        r"subprocess",
    ]
    flagged = False
    for pat in injection_patterns:
        if _re.search(pat, text, _re.IGNORECASE):
            flagged = True
            text = _re.sub(pat, "[removed]", text, flags=_re.IGNORECASE)

    # Strip HTML tags
    text = _re.sub(r"<[^>]+>", "", text)

    return text.strip(), flagged
