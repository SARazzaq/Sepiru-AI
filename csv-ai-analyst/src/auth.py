"""
Sepiru AI — Single-page login gate.
Password + Math CAPTCHA + Honeypot — all on one screen, one submit.
Honeypot is a real hidden HTML field — invisible to humans, filled by bots.
"""
import os
import random
import time
import streamlit as st
import streamlit.components.v1 as components


def _get_password() -> str:
    try:
        p = st.secrets.get("APP_PASSWORD", "")
        if p:
            return p
    except Exception:
        pass
    return os.getenv("APP_PASSWORD", "sepiru")


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


def require_auth():
    if st.session_state.get("_auth"):
        return

    # Generate captcha on first load
    if "_cap_q" not in st.session_state:
        _new_captcha()

    # Expire captcha after 5 min
    if time.time() - st.session_state.get("_cap_ts", 0) > 300:
        _new_captcha()

    q   = st.session_state["_cap_q"]
    ans = st.session_state["_cap_ans"]

    # Hide all Streamlit chrome
    st.markdown("""
    <style>
    #MainMenu,footer,header,
    [data-testid="stToolbar"],[data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    section[data-testid="stSidebar"]{display:none!important;}
    html,body{margin:0!important;padding:0!important;}
    .stApp{background:#000!important;}
    .main .block-container{
        padding:0!important;max-width:100%!important;
        min-height:100vh!important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Render the full login page inside components.html
    # This gives us full DOM control — honeypot is a real hidden input
    result = components.html(
        _login_html(q),
        height=700,
        scrolling=False
    )

    # Read submitted values from query params (set by the form JS)
    params = st.query_params
    submitted_pwd = params.get("_spw", "")
    submitted_cap = params.get("_sca", "")
    submitted_hp  = params.get("_shp", "")
    submitted_ref = params.get("_ref", "")

    if submitted_pwd:
        error = None

        # 1. Honeypot check — bots fill it, humans don't
        if submitted_hp:
            error = "bot"

        # 2. Password check
        elif submitted_pwd != _get_password():
            error = "wrong_password"

        # 3. Math captcha check
        else:
            try:
                given = int(submitted_cap.strip())
            except (ValueError, AttributeError):
                given = None
            if given != ans:
                error = "wrong_captcha"
                _new_captcha()  # regenerate on wrong answer

        if error is None:
            # All checks passed
            st.session_state["_auth"] = True
            st.query_params.clear()
            st.rerun()
        else:
            # Show error — re-render with error message
            _new_captcha()
            q   = st.session_state["_cap_q"]
            err_msg = {
                "bot":           "🤖 Automated access detected.",
                "wrong_password": "✕ Incorrect access key.",
                "wrong_captcha":  "✕ Wrong answer. New problem generated.",
            }.get(error, "Please try again.")

            st.markdown(f"""
            <style>
            .sep-err-banner{{
                position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);
                background:rgba(244,63,94,.12);border:1px solid rgba(244,63,94,.3);
                border-radius:10px;padding:.7rem 1.5rem;
                font-family:'Space Grotesk',sans-serif;font-size:.8rem;
                color:#f87171;letter-spacing:.3px;z-index:9999;
                animation:sfadeUp .3s ease both;
            }}
            @keyframes sfadeUp{{
                from{{opacity:0;transform:translateX(-50%) translateY(10px);}}
                to{{opacity:1;transform:translateX(-50%) translateY(0);}}
            }}
            </style>
            <div class="sep-err-banner">{err_msg}</div>
            """, unsafe_allow_html=True)

            st.query_params.clear()

    st.stop()


def _login_html(captcha_q: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&family=Cormorant+Garamond:ital,wght@0,300;1,300;1,400&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{
    width:100%;height:100%;
    background:#000;
    font-family:'Space Grotesk',sans-serif;
    overflow:hidden;
}}
canvas{{position:fixed;inset:0;pointer-events:none;z-index:0;}}

.wrap{{
    position:relative;z-index:10;
    min-height:100vh;
    display:flex;flex-direction:column;
    align-items:center;justify-content:center;
    padding:1.5rem 1rem;
    gap:0;
}}

/* Hero */
.eyebrow{{
    font-size:.6rem;font-weight:500;letter-spacing:5px;text-transform:uppercase;
    color:rgba(201,168,76,.5);margin-bottom:.8rem;text-align:center;
    animation:fadeUp .8s ease both;
}}
.name{{
    font-family:'Cormorant Garamond',serif;
    font-size:clamp(3.5rem,9vw,6rem);
    font-weight:300;font-style:italic;line-height:.95;
    background:linear-gradient(135deg,#fff 0%,#f5e080 25%,#c9a84c 55%,#f5e8b8 80%,#fff 100%);
    background-size:200% auto;
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    filter:drop-shadow(0 0 40px rgba(201,168,76,.3));
    margin-bottom:.8rem;text-align:center;
    animation:fadeUp .9s ease .05s both, goldFlow 4s linear 1s infinite;
}}
.tagline{{
    font-size:clamp(.78rem,1.8vw,.92rem);font-weight:300;
    color:rgba(255,255,255,.38);line-height:1.65;
    text-align:center;margin-bottom:.6rem;
    animation:fadeUp .8s ease .15s both;
}}
.tagline span{{color:rgba(201,168,76,.8);font-weight:500;}}
.divider{{
    width:40px;height:1px;
    background:linear-gradient(90deg,transparent,rgba(201,168,76,.5),transparent);
    margin:.6rem auto 1.2rem;
    animation:fadeUp .7s ease .2s both;
}}

/* Card */
.card{{
    width:100%;max-width:380px;
    background:linear-gradient(160deg,rgba(12,12,32,.97) 0%,rgba(8,8,24,.99) 100%);
    border:1px solid rgba(201,168,76,.18);border-radius:20px;
    padding:1.8rem 1.8rem 1.6rem;
    position:relative;overflow:hidden;
    animation:fadeUp .8s ease .3s both;
    backdrop-filter:blur(20px);
}}
.card::before{{
    content:'';position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(201,168,76,.2) 20%,
        rgba(248,230,140,.8) 50%,rgba(201,168,76,.2) 80%,transparent);
}}

/* Field label */
.field-label{{
    font-size:.58rem;font-weight:500;letter-spacing:3px;text-transform:uppercase;
    color:rgba(201,168,76,.4);margin-bottom:.5rem;display:block;
}}

/* Inputs */
input[type="password"],
input[type="text"].visible-input{{
    width:100%;
    background:rgba(255,255,255,.04);
    border:1px solid rgba(201,168,76,.22);
    border-radius:10px;color:#fff;
    font-family:'Space Grotesk',sans-serif;
    font-size:.95rem;letter-spacing:4px;
    text-align:center;padding:.7rem 1rem;
    caret-color:#c9a84c;
    transition:border-color .3s ease,box-shadow .3s ease;
    outline:none;
    margin-bottom:1rem;
}}
input[type="password"]:focus,
input[type="text"].visible-input:focus{{
    border-color:rgba(201,168,76,.55);
    box-shadow:0 0 0 3px rgba(201,168,76,.08);
}}
input::placeholder{{color:rgba(255,255,255,.12);letter-spacing:5px;}}

/* Math box */
.math-box{{
    background:rgba(201,168,76,.05);
    border:1px solid rgba(201,168,76,.14);
    border-radius:12px;padding:1rem;
    text-align:center;margin-bottom:1rem;
}}
.math-label{{
    font-size:.55rem;font-weight:500;letter-spacing:3px;text-transform:uppercase;
    color:rgba(201,168,76,.35);margin-bottom:.5rem;
}}
.math-eq{{
    font-family:'Cormorant Garamond',serif;
    font-size:2.4rem;font-weight:400;font-style:italic;
    background:linear-gradient(135deg,#f5e080,#c9a84c);
    background-size:200% auto;
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    filter:drop-shadow(0 0 16px rgba(201,168,76,.35));
    line-height:1;margin-bottom:.3rem;
    animation:goldFlow 3s linear infinite;
}}
.math-hint{{font-size:.58rem;color:rgba(255,255,255,.18);letter-spacing:.5px;}}

/* Honeypot — TRULY invisible: no size, no position, no interaction */
.hp-field{{
    position:absolute;
    left:-9999px;top:-9999px;
    width:1px;height:1px;
    opacity:0;pointer-events:none;
    tab-index:-1;
    overflow:hidden;
}}

/* Submit button */
button[type="submit"]{{
    width:100%;
    background:linear-gradient(135deg,#c9a84c 0%,#f5e080 50%,#c9a84c 100%);
    background-size:200% auto;
    color:#000;border:none;border-radius:10px;
    font-family:'Space Grotesk',sans-serif;
    font-size:.68rem;font-weight:600;
    letter-spacing:3px;text-transform:uppercase;
    padding:.75rem;cursor:pointer;
    box-shadow:0 4px 24px rgba(201,168,76,.22);
    transition:box-shadow .3s ease,transform .2s ease;
    animation:goldFlow 3s linear infinite;
}}
button[type="submit"]:hover{{
    box-shadow:0 8px 40px rgba(201,168,76,.45);
    transform:translateY(-2px);
}}
button[type="submit"]:active{{transform:scale(.96);}}

.footer{{
    font-size:.52rem;color:rgba(255,255,255,.1);
    letter-spacing:2px;text-transform:uppercase;
    text-align:center;margin-top:.8rem;
    animation:fadeUp .7s ease .5s both;
}}

@keyframes fadeUp{{
    from{{opacity:0;transform:translateY(18px);filter:blur(4px);}}
    to{{opacity:1;transform:translateY(0);filter:blur(0);}}
}}
@keyframes goldFlow{{
    0%{{background-position:0% center;}}
    100%{{background-position:200% center;}}
}}
</style>
</head>
<body>
<canvas id="c"></canvas>

<div class="wrap">
    <div class="eyebrow">Data Intelligence Platform</div>
    <div class="name">Sepiru AI</div>
    <div class="tagline">
        Most tools make you work for the answer.<br>
        <span>Sepiru AI just answers.</span>
    </div>
    <div class="divider"></div>

    <form class="card" id="loginForm" onsubmit="handleSubmit(event)">

        <!-- Password -->
        <label class="field-label">Access Key</label>
        <input type="password" id="pwd" placeholder="· · · · · · · ·" autocomplete="current-password" required>

        <!-- Math CAPTCHA -->
        <div class="math-box">
            <div class="math-label">Verify you're human</div>
            <div class="math-eq">{captcha_q} = ?</div>
            <div class="math-hint">Enter the answer below</div>
        </div>
        <input type="text" class="visible-input" id="cap"
               placeholder="Answer" autocomplete="off" required
               inputmode="numeric" pattern="[0-9-]*">

        <!-- Honeypot — completely hidden, only bots fill this -->
        <div class="hp-field" aria-hidden="true">
            <input type="text" id="hp" name="website" tabindex="-1"
                   autocomplete="off" value="">
        </div>

        <button type="submit">Enter →</button>
    </form>

    <div class="footer">✦ Authorised access only &nbsp;·&nbsp; Protected by custom CAPTCHA</div>
</div>

<script>
/* ── Aurora + particles ── */
(function(){{
    const cv=document.getElementById('c');
    const cx=cv.getContext('2d');
    let W,H,pts,mx=9999,my=9999;
    function resize(){{W=cv.width=window.innerWidth;H=cv.height=window.innerHeight;}}
    resize();window.addEventListener('resize',resize);
    document.addEventListener('mousemove',e=>{{mx=e.clientX;my=e.clientY;}});
    const BLOBS=[
        {{x:.5,y:-.05,rx:.85,ry:.5,h:42,s:80,a:.13,sp:.0002,ph:0}},
        {{x:.08,y:.9,rx:.5,ry:.35,h:258,s:70,a:.07,sp:.0003,ph:2.1}},
        {{x:.92,y:.8,rx:.45,ry:.3,h:162,s:65,a:.06,sp:.0004,ph:4.2}},
    ];
    function initPts(){{
        const N=Math.floor(W*H/18000);
        pts=Array.from({{length:N}},()=>(({{
            x:Math.random()*W,y:Math.random()*H,
            vx:(Math.random()-.5)*.2,vy:(Math.random()-.5)*.2,
            r:Math.random()*1.4+.3,
            ph:Math.random()*Math.PI*2,spd:.01+Math.random()*.016,
        }})));
    }}
    initPts();window.addEventListener('resize',initPts);
    let t=0;
    function draw(){{
        requestAnimationFrame(draw);cx.clearRect(0,0,W,H);t+=.007;
        BLOBS.forEach(b=>{{
            const ox=Math.sin(t*b.sp*1000+b.ph)*.06;
            const oy=Math.cos(t*b.sp*800+b.ph)*.04;
            const px=(b.x+ox)*W,py=(b.y+oy)*H;
            const a=b.a*(.6+Math.sin(t+b.ph)*.4);
            const g=cx.createRadialGradient(px,py,0,px,py,Math.max(W,H)*b.rx);
            g.addColorStop(0,`hsla(${{b.h}},${{b.s}}%,60%,${{a}})`);
            g.addColorStop(.5,`hsla(${{b.h}},${{b.s}}%,40%,${{a*.4}})`);
            g.addColorStop(1,'transparent');
            cx.fillStyle=g;cx.fillRect(0,0,W,H);
        }});
        for(let i=0;i<pts.length;i++){{
            const a=pts[i];
            for(let j=i+1;j<pts.length;j++){{
                const b=pts[j];
                const dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy;
                if(d2<110*110){{
                    cx.beginPath();
                    cx.strokeStyle=`rgba(201,168,76,${{.08*(1-Math.sqrt(d2)/110)}})`;
                    cx.lineWidth=.3;cx.moveTo(a.x,a.y);cx.lineTo(b.x,b.y);cx.stroke();
                }}
            }}
        }}
        for(const p of pts){{
            p.ph+=p.spd;
            const g=.38+Math.sin(p.ph)*.25;
            const dx=p.x-mx,dy=p.y-my,d2=dx*dx+dy*dy;
            if(d2<8100){{const d=Math.sqrt(d2);const f=(90-d)/90*.35;p.vx+=dx/d*f;p.vy+=dy/d*f;}}
            p.vx*=.992;p.vy*=.992;
            cx.beginPath();cx.arc(p.x,p.y,p.r,0,Math.PI*2);
            cx.fillStyle=`rgba(201,168,76,${{g}})`;cx.fill();
            p.x+=p.vx;p.y+=p.vy;
            if(p.x<-10)p.x=W+10;if(p.x>W+10)p.x=-10;
            if(p.y<-10)p.y=H+10;if(p.y>H+10)p.y=-10;
        }}
    }}
    draw();
}})();

/* ── Form submit — send values to Streamlit via query params ── */
function handleSubmit(e){{
    e.preventDefault();
    const pwd = document.getElementById('pwd').value;
    const cap = document.getElementById('cap').value;
    const hp  = document.getElementById('hp').value;
    // Send to parent Streamlit via URL query params
    const url = new URL(window.parent.location.href);
    url.searchParams.set('_spw', pwd);
    url.searchParams.set('_sca', cap);
    url.searchParams.set('_shp', hp);
    url.searchParams.set('_ref', Date.now());
    window.parent.location.href = url.toString();
}}
</script>
</body>
</html>"""
