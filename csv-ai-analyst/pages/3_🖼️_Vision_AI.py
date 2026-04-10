"""
Vision AI — powered by Gemini 1.5 Flash (free, cloud-ready).
No Ollama required. Works on Streamlit Cloud.
Free tier: 1,500 req/day, 15 RPM.
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.ui_components import load_all_styles
load_all_styles("assets")

from src.auth import require_auth
require_auth()

st.markdown("""
<div class='app-header'>
    <h1>🖼️ Vision <span>AI</span></h1>
    <p>Analyze images with Gemini Vision &nbsp;·&nbsp; Free &nbsp;·&nbsp; No setup required</p>
</div>
""", unsafe_allow_html=True)

# ── Gemini Vision setup ───────────────────────────────────────────────────────
def _get_secret(key):
    try:
        v = st.secrets.get(key, "")
        if v: return v
    except Exception:
        pass
    return os.getenv(key, "")

GEMINI_KEY = _get_secret("GEMINI_API_KEY")

if not GEMINI_KEY:
    st.error("GEMINI_API_KEY not set. Add it to Streamlit secrets.")
    st.code('GEMINI_API_KEY = "AIza_your_key_here"', language="toml")
    st.stop()

try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    vision_model = genai.GenerativeModel("gemini-2.0-flash")
except Exception as e:
    st.error(f"Failed to load Gemini: {e}")
    st.stop()

import PIL.Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

st.markdown("""
<div class="status-pill" style="margin-bottom:1rem;">
    <span class="live-dot"></span>
    Gemini 1.5 Flash &nbsp;·&nbsp; Vision Ready
</div>
""", unsafe_allow_html=True)

mode = st.radio("Mode", ["🖼️ Single Image Chat", "📁 Batch Image Analysis"],
                horizontal=True)

# ─────────────────────────────────────────────────────────────────────────────
# MODE 1 — SINGLE IMAGE CHAT
# ─────────────────────────────────────────────────────────────────────────────
if mode == "🖼️ Single Image Chat":
    st.subheader("🖼️ Chat with an Image")

    uploaded_img = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "bmp", "webp", "gif"]
    )

    if uploaded_img:
        size_mb = len(uploaded_img.getvalue()) / (1024 * 1024)
        if size_mb > 20:
            st.error(f"Image too large ({size_mb:.1f} MB). Max 20 MB.")
            st.stop()

        img_bytes = uploaded_img.getvalue()
        pil_img   = PIL.Image.open(uploaded_img)

        col_img, col_chat = st.columns([1, 2])

        with col_img:
            st.image(pil_img, caption=uploaded_img.name, use_container_width=True)
            st.caption(f"{size_mb:.2f} MB · {pil_img.size[0]}×{pil_img.size[1]}px")

        with col_chat:
            if "vision_chat" not in st.session_state:
                st.session_state.vision_chat = []

            for msg in st.session_state.vision_chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            vision_input = st.chat_input("Ask anything about this image…")

            if vision_input:
                with st.chat_message("user"):
                    st.markdown(vision_input)
                st.session_state.vision_chat.append(
                    {"role": "user", "content": vision_input}
                )

                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    response    = ""
                    try:
                        result = vision_model.generate_content(
                            [vision_input, pil_img], stream=True
                        )
                        for chunk in result:
                            if chunk.text:
                                response += chunk.text
                                placeholder.markdown(response + "▌")
                    except Exception as e:
                        response = f"❌ Error: {e}"
                    placeholder.markdown(response)

                st.session_state.vision_chat.append(
                    {"role": "assistant", "content": response}
                )

            if st.session_state.vision_chat:
                if st.button("🗑️ Clear Chat", key="clear_vision"):
                    st.session_state.vision_chat = []
                    st.rerun()

            with st.expander("💡 Suggested questions"):
                for s in [
                    "What is in this image?",
                    "Describe the colors and mood.",
                    "What objects can you identify?",
                    "Is there any text in this image?",
                    "What category does this image belong to?",
                    "Describe this image for someone who cannot see it.",
                ]:
                    if st.button(s, key=f"vis_{s}"):
                        st.session_state.vision_chat.append(
                            {"role": "user", "content": s}
                        )
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# MODE 2 — BATCH ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.subheader("📁 Batch Image Analysis")
    st.info("Upload multiple images and analyze them all with one prompt.")

    uploaded_files = st.file_uploader(
        "Upload images (max 10)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.warning("Max 10 images at a time. Using first 10.")
            uploaded_files = uploaded_files[:10]

        st.success(f"✅ {len(uploaded_files)} image(s) loaded")

        # Preview grid
        cols = st.columns(min(4, len(uploaded_files)))
        for i, f in enumerate(uploaded_files):
            with cols[i % 4]:
                st.image(f, caption=f.name, use_container_width=True)

        st.markdown("---")

        analysis_type = st.selectbox("Analysis Type", [
            "General description",
            "Classify the image content",
            "Detect objects present",
            "Describe colors and composition",
            "Identify any text in the image",
            "Custom prompt",
        ])

        prompts = {
            "General description":             "Describe this image in detail.",
            "Classify the image content":      "What category does this image belong to? Give a single label.",
            "Detect objects present":           "List all objects visible in this image.",
            "Describe colors and composition":  "Describe the colors, lighting, and composition.",
            "Identify any text in the image":   "Extract and list all text visible in this image.",
            "Custom prompt": "",
        }

        if analysis_type == "Custom prompt":
            prompt = st.text_area("Enter your prompt:", height=80)
        else:
            prompt = prompts[analysis_type]
            st.info(f"Prompt: *{prompt}*")

        if st.button("▶️ Analyze All Images", type="primary", use_container_width=True):
            if not prompt:
                st.warning("Please enter a prompt.")
            else:
                results  = []
                progress = st.progress(0)
                status   = st.empty()

                for i, f in enumerate(uploaded_files):
                    status.text(f"Analyzing {f.name}… ({i+1}/{len(uploaded_files)})")
                    try:
                        pil_img = PIL.Image.open(f)
                        resp    = vision_model.generate_content([prompt, pil_img])
                        results.append({"Image": f.name, "Analysis": resp.text})
                    except Exception as e:
                        results.append({"Image": f.name, "Analysis": f"Error: {e}"})
                    progress.progress((i + 1) / len(uploaded_files))

                progress.empty()
                status.empty()

                import pandas as pd
                result_df = pd.DataFrame(results)
                st.success(f"✅ Analyzed {len(results)} images!")
                st.dataframe(result_df, use_container_width=True, hide_index=True)

                csv = result_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Results CSV", csv,
                                   file_name="vision_analysis.csv",
                                   mime="text/csv", use_container_width=True)
