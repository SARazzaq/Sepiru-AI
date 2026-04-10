"""
Sepiru AI — Premium 3-step authentication gate.
Step 1: Password
Step 2: Math CAPTCHA (custom-coded, no third-party)
Step 3: Honeypot bot trap
All free, no external services.
"""
import os
import random
import time
import streamlit as st


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_password() -> str:
    try:
        p = st.secrets.get("APP_PASSWORD", "")
        if p:
            return p
    except Exception:
        pass
    return os.getenv("APP_PASSWORD", "sepiru")


def _new_captcha():
    """Generate a random math problem and store answer in session."""
    ops = ['+', '-', '×']
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


# ── Main gate ─────────────────────────────────────────────────────────────────

def require_auth():
    if st.session_state.get("_auth"):
        return

    # Inject styles + canvas
    st.markdown(_css(), unsafe_allow_html=True)
    st.markdown(_canvas(), unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="sep-hero">
        <div class="sep-eyebrow">Data Intelligence Platform</div>
        <div class="sep-name">Sepiru AI</div>
        <div class="sep-tagline">
            Most tools make you work for the answer.
            <span class="sep-accent">Sepiru AI just answers.</span>
        </div>
        <div class="sep-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    step = st.session_state.get("_auth_step", 1)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:

        # ── STEP 1 — Password ─────────────────────────────────────────────────
        if step == 1:
            st.markdown('<div class="sep-card">', unsafe_allow_html=True)
            st.markdown('<div class="sep-step-label">Step 1 of 2 &nbsp;·&nbsp; Access Key</div>', unsafe_allow_html=True)

            # Honeypot — hidden field, bots fill it, humans don't see it
            hp = st.text_input("Leave this blank", value="",
                               key="_hp", label_visibility="collapsed")
            st.markdown("""
            <style>
            /* Hide honeypot from humans — bots ignore CSS */
            div[data-testid="stTextInput"]:has(input[data-testid="stTextInput"]:first-of-type) {
                display:none!important;
            }
            </style>
            """, unsafe_allow_html=True)

            pwd = st.text_input("Access Key", type="password",
                                placeholder="· · · · · · · ·",
                                label_visibility="collapsed",
                                key="_pw")
            btn = st.button("Continue →", use_container_width=True, key="_pw_btn")

            if btn:
                # Honeypot check — if filled, it's a bot
                if hp:
                    st.markdown('<div class="sep-err">🤖 Bot detected. Access denied.</div>',
                                unsafe_allow_html=True)
                elif not pwd:
                    st.markdown('<div class="sep-err">Please enter your access key.</div>',
                                unsafe_allow_html=True)
                elif pwd == _get_password():
                    _new_captcha()
                    st.session_state["_auth_step"] = 2
                    st.rerun()
                else:
                    st.markdown('<div class="sep-err">✕ &nbsp;Incorrect access key.</div>',
                                unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # ── STEP 2 — Math CAPTCHA ─────────────────────────────────────────────
        elif step == 2:
            # Expire captcha after 5 minutes
            if time.time() - st.session_state.get("_cap_ts", 0) > 300:
                _new_captcha()

            q   = st.session_state.get("_cap_q", "")
            ans = st.session_state.get("_cap_ans", 0)

            st.markdown('<div class="sep-card">', unsafe_allow_html=True)
            st.markdown('<div class="sep-step-label">Step 2 of 2 &nbsp;·&nbsp; Verify You\'re Human</div>',
                        unsafe_allow_html=True)

            # Visual math problem
            st.markdown(f"""
            <div class="sep-math-box">
                <div class="sep-math-label">Solve to continue</div>
                <div class="sep-math-eq">{q} = ?</div>
                <div class="sep-math-hint">Enter the answer below</div>
            </div>
            """, unsafe_allow_html=True)

            user_ans = st.text_input("Answer", placeholder="Your answer",
                                     label_visibility="collapsed",
                                     key="_cap_input")
            c1, c2 = st.columns(2)
            with c1:
                verify_btn = st.button("Verify →", use_container_width=True,
                                       type="primary", key="_cap_btn")
            with c2:
                refresh_btn = st.button("New problem ↺", use_container_width=True,
                                        key="_cap_refresh")

            if refresh_btn:
                _new_captcha()
                st.rerun()

            if verify_btn:
                try:
                    given = int(str(user_ans).strip())
                except ValueError:
                    st.markdown('<div class="sep-err">Please enter a number.</div>',
                                unsafe_allow_html=True)
                else:
                    if given == ans:
                        st.session_state["_auth"]      = True
                        st.session_state["_auth_step"] = 1
                        st.rerun()
                    else:
                        _new_captcha()  # regenerate on wrong answer
                        st.markdown(
                            '<div class="sep-err">✕ &nbsp;Wrong answer. New problem generated.</div>',
                            unsafe_allow_html=True)
                        st.rerun()

            # Back button
            if st.button("← Back", key="_cap_back"):
                st.session_state["_auth_step"] = 1
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown('<div class="sep-footer">✦ Authorised access only &nbsp;·&nbsp; Protected by custom CAPTCHA</div>',
                unsafe_allow_html=True)
    st.stop()


# ── CSS ───────────────────────────────────────────────────────────────────────

def _css() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&family=Cormorant+Garamond:ital,wght@0,300;1,300;1,400&display=swap');

    #MainMenu,footer,header,
    [data-testid="stToolbar"],[data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    section[data-testid="stSidebar"] { display:none!important; }

    html,body { margin:0!important;padding:0!important;overflow-x:hidden!important; }
    .stApp { background:#000!important; }

    .main .block-container {
        padding:1rem 1rem 2rem!important;
        max-width:100%!important;
        min-height:100vh!important;
        display:flex!important;
        flex-direction:column!important;
        align-items:center!important;
        justify-content:center!important;
    }

    /* ── Hero ── */
    .sep-hero {
        text-align:center;position:relative;z-index:10;
        padding:0 1rem;margin-bottom:.5rem;
        animation:sfadeUp .9s cubic-bezier(.22,1,.36,1) both;
    }
    .sep-eyebrow {
        font-family:'Space Grotesk',sans-serif;
        font-size:.6rem;font-weight:500;letter-spacing:5px;text-transform:uppercase;
        color:rgba(201,168,76,.5);margin-bottom:.8rem;
    }
    .sep-name {
        font-family:'Cormorant Garamond',serif;
        font-size:clamp(3.5rem,9vw,6.5rem);
        font-weight:300;font-style:italic;line-height:.95;
        background:linear-gradient(135deg,#fff 0%,#f5e080 25%,#c9a84c 55%,#f5e8b8 80%,#fff 100%);
        background-size:200% auto;
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        animation:sfadeUp .9s ease .08s both,sgoldFlow 4s linear 1s infinite;
        filter:drop-shadow(0 0 40px rgba(201,168,76,.3));
        margin-bottom:.9rem;
    }
    .sep-tagline {
        font-family:'Space Grotesk',sans-serif;
        font-size:clamp(.8rem,1.8vw,.95rem);font-weight:300;
        color:rgba(255,255,255,.4);line-height:1.7;margin-bottom:.2rem;
    }
    .sep-accent { color:rgba(201,168,76,.85);font-weight:500; }
    .sep-divider {
        width:40px;height:1px;
        background:linear-gradient(90deg,transparent,rgba(201,168,76,.5),transparent);
        margin:.8rem auto 0;
    }

    /* ── Card ── */
    .sep-card {
        background:linear-gradient(160deg,rgba(12,12,32,.96) 0%,rgba(8,8,24,.98) 100%);
        border:1px solid rgba(201,168,76,.18);border-radius:20px;
        padding:2rem 2rem 1.8rem;position:relative;overflow:hidden;
        animation:sfadeUp .8s cubic-bezier(.22,1,.36,1) .3s both;
        backdrop-filter:blur(20px);margin-bottom:.5rem;
    }
    .sep-card::before {
        content:'';position:absolute;top:0;left:0;right:0;height:1px;
        background:linear-gradient(90deg,transparent,rgba(201,168,76,.2) 20%,
            rgba(248,230,140,.8) 50%,rgba(201,168,76,.2) 80%,transparent);
    }

    /* ── Step label ── */
    .sep-step-label {
        font-family:'Space Grotesk',sans-serif;
        font-size:.58rem;font-weight:500;letter-spacing:3px;text-transform:uppercase;
        color:rgba(201,168,76,.4);text-align:center;margin-bottom:1.2rem;
    }

    /* ── Math box ── */
    .sep-math-box {
        background:rgba(201,168,76,.05);
        border:1px solid rgba(201,168,76,.15);
        border-radius:14px;padding:1.5rem 1rem;
        text-align:center;margin-bottom:1.2rem;
        position:relative;overflow:hidden;
    }
    .sep-math-box::before {
        content:'';position:absolute;inset:0;
        background:radial-gradient(ellipse at 50% 0%,rgba(201,168,76,.08) 0%,transparent 65%);
    }
    .sep-math-label {
        font-family:'Space Grotesk',sans-serif;
        font-size:.58rem;font-weight:500;letter-spacing:3px;text-transform:uppercase;
        color:rgba(201,168,76,.4);margin-bottom:.8rem;
    }
    .sep-math-eq {
        font-family:'Cormorant Garamond',serif;
        font-size:2.8rem;font-weight:400;font-style:italic;
        background:linear-gradient(135deg,#f5e080,#c9a84c);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 20px rgba(201,168,76,.4));
        line-height:1;margin-bottom:.5rem;
        animation:sfadeUp .5s ease both,sgoldFlow 3s linear infinite;
        background-size:200% auto;
    }
    .sep-math-hint {
        font-family:'Space Grotesk',sans-serif;
        font-size:.6rem;color:rgba(255,255,255,.2);letter-spacing:1px;
    }

    /* ── Input ── */
    .stTextInput > div > div > input {
        background:rgba(255,255,255,.04)!important;
        border:1px solid rgba(201,168,76,.22)!important;
        border-radius:10px!important;color:#fff!important;
        font-family:'Space Grotesk',sans-serif!important;
        font-size:1rem!important;letter-spacing:6px!important;
        text-align:center!important;padding:.75rem 1rem!important;
        caret-color:#c9a84c!important;transition:all .3s ease!important;
    }
    .stTextInput > div > div > input:focus {
        border-color:rgba(201,168,76,.55)!important;
        box-shadow:0 0 0 3px rgba(201,168,76,.08)!important;
        outline:none!important;
    }
    .stTextInput > div > div > input::placeholder {
        color:rgba(255,255,255,.1)!important;letter-spacing:6px!important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background:linear-gradient(135deg,#c9a84c 0%,#f5e080 50%,#c9a84c 100%)!important;
        background-size:200% auto!important;color:#000!important;border:none!important;
        border-radius:10px!important;font-family:'Space Grotesk',sans-serif!important;
        font-size:.68rem!important;font-weight:600!important;
        letter-spacing:3px!important;text-transform:uppercase!important;
        padding:.75rem!important;margin-top:.4rem!important;
        box-shadow:0 4px 24px rgba(201,168,76,.22)!important;
        transition:all .3s ease!important;animation:sgoldFlow 3s linear infinite!important;
    }
    .stButton > button:hover {
        box-shadow:0 8px 40px rgba(201,168,76,.45)!important;
        transform:translateY(-2px)!important;
    }
    /* Back button — subtle */
    .stButton > button[kind="secondary"] {
        background:transparent!important;
        border:1px solid rgba(201,168,76,.2)!important;
        color:rgba(201,168,76,.6)!important;
        box-shadow:none!important;animation:none!important;
        font-size:.62rem!important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color:rgba(201,168,76,.4)!important;
        color:rgba(201,168,76,.9)!important;
        transform:none!important;box-shadow:none!important;
    }

    /* ── Error / success ── */
    .sep-err {
        text-align:center;font-family:'Space Grotesk',sans-serif;
        font-size:.75rem;color:#f87171;margin-top:.6rem;
        padding:.5rem .8rem;background:rgba(244,63,94,.07);
        border:1px solid rgba(244,63,94,.15);border-radius:8px;
        animation:sfadeUp .3s ease both;
    }

    /* ── Footer ── */
    .sep-footer {
        font-family:'Space Grotesk',sans-serif;
        font-size:.55rem;color:rgba(255,255,255,.12);
        letter-spacing:2px;text-transform:uppercase;
        text-align:center;margin-top:.8rem;
        animation:sfadeUp .8s ease .6s both;
    }

    /* ── Honeypot — invisible to humans, bots fill it ── */
    div[data-testid="stTextInput"]:first-of-type {
        position:absolute!important;
        left:-9999px!important;top:-9999px!important;
        width:1px!important;height:1px!important;
        overflow:hidden!important;opacity:0!important;
        pointer-events:none!important;tab-index:-1!important;
    }

    /* ── Keyframes ── */
    @keyframes sfadeUp {
        from{opacity:0;transform:translateY(20px);filter:blur(4px);}
        to{opacity:1;transform:translateY(0);filter:blur(0);}
    }
    @keyframes sgoldFlow {
        0%{background-position:0% center;}
        100%{background-position:200% center;}
    }
    </style>
    """


# ── Canvas aurora background ──────────────────────────────────────────────────

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
            {x:.5,y:-.05,rx:.85,ry:.5,h:42, s:80,a:.13,sp:.0002,ph:0},
            {x:.08,y:.9, rx:.5, ry:.35,h:258,s:70,a:.07,sp:.0003,ph:2.1},
            {x:.92,y:.8, rx:.45,ry:.3,h:162,s:65,a:.06,sp:.0004,ph:4.2},
        ];
        function initPts(){
            const N=Math.floor(W*H/18000);
            pts=Array.from({length:N},()=>({
                x:Math.random()*W,y:Math.random()*H,
                vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,
                r:Math.random()*1.4+.3,
                ph:Math.random()*Math.PI*2,spd:.01+Math.random()*.016,
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
