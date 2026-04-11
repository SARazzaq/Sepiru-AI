"""
Logbook to CSV — Convert handwritten logbook pages to structured CSV.
Uses Groq LLaMA 4 Scout Vision (free) for OCR + structuring.
No extra libraries needed — vision model reads AND structures in one shot.
"""

import streamlit as st
import pandas as pd
import base64
import json
import io
import re
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

from src.ui_components import load_all_styles
load_all_styles("assets")

from src.auth import require_auth
require_auth()

st.markdown("""
<div class='app-header'>
    <h1>📖 Logbook <span>to CSV</span></h1>
    <p>Upload photos of handwritten records &nbsp;·&nbsp; AI reads &amp; structures them &nbsp;·&nbsp; Download as CSV</p>
</div>""", unsafe_allow_html=True)


# ── Groq vision client ────────────────────────────────────────────────────────
def _get_secret(key):
    try:
        v = st.secrets.get(key, "")
        if v: return v
    except Exception:
        pass
    return os.getenv(key, "")


GROQ_KEY    = _get_secret("GROQ_API_KEY")
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

if not GROQ_KEY:
    st.error("GROQ_API_KEY not set. Add it to Streamlit secrets.")
    st.stop()

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error(f"Failed to load Groq: {e}")
    st.stop()

MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png",  ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def extract_table_from_image(image_bytes: bytes, mime: str,
                              hint: str = "") -> str:
    """
    Send logbook page image to LLaMA 4 Scout.
    Returns raw text extracted and structured as CSV rows.
    """
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    hint_text = f"\nAdditional context about this logbook: {hint}" if hint else ""

    prompt = f"""You are an expert OCR and data extraction system.

This image contains a handwritten logbook page with tabular or structured data.{hint_text}

Your task:
1. Read ALL handwritten text carefully, including headers and every row of data.
2. Identify the column headers (if present) or infer them from context.
3. Extract every data row exactly as written.
4. Return the data as valid CSV format ONLY — no explanation, no markdown, no code blocks.
5. First line must be the header row.
6. Use comma as delimiter.
7. If a cell is empty or illegible, use empty string.
8. Preserve numbers exactly as written (dates, amounts, quantities).

Return ONLY the CSV data, nothing else."""

    try:
        resp = groq_client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{b64}"}}
                ]
            }],
            max_tokens=2048,
            temperature=0.1,  # low temp for accuracy
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"


def clean_csv_text(raw: str) -> str:
    """Remove markdown code fences if model added them."""
    raw = re.sub(r"```(?:csv)?\n?", "", raw)
    raw = re.sub(r"```", "", raw)
    return raw.strip()


def parse_csv_text(csv_text: str) -> pd.DataFrame | None:
    """Parse CSV string into DataFrame."""
    try:
        return pd.read_csv(io.StringIO(csv_text))
    except Exception:
        return None


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="glass-card" style="margin-bottom:1.5rem;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:.85rem;
color:rgba(255,255,255,.55);line-height:1.8;">
<strong style="color:#c9a84c;">How it works:</strong><br>
1. Upload one or more photos of your handwritten logbook pages<br>
2. AI reads the handwriting and extracts all data into structured rows<br>
3. All pages are merged into a single CSV file<br>
4. Download the CSV and use it anywhere in Sepiru AI
</div>
</div>
""", unsafe_allow_html=True)

# Hint input
hint = st.text_input(
    "Describe your logbook (optional but improves accuracy)",
    placeholder="e.g. Sales register with date, item name, quantity, price — or Patient records with name, age, diagnosis",
    help="Tell the AI what kind of data is in your logbook for better column detection"
)

# File uploader
uploaded_pages = st.file_uploader(
    "Upload logbook page photos (jpg, png, webp)",
    type=["jpg", "jpeg", "png", "webp", "bmp"],
    accept_multiple_files=True,
    help="Upload pages in order. Each image = one page of your logbook."
)

if not uploaded_pages:
    st.markdown("""
    <div class="upload-cta" style="margin-top:1rem;">
        <h2>No logbook? No problem.</h2>
        <p>Take photos of your handwritten register, account book, patient records,<br>
        field notes, or any structured handwritten data — and we'll digitize it.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.success(f"✅ {len(uploaded_pages)} page(s) uploaded")

# Preview
st.subheader("📷 Page Preview")
preview_cols = st.columns(min(4, len(uploaded_pages)))
for i, f in enumerate(uploaded_pages):
    with preview_cols[i % 4]:
        st.image(f.getvalue(), caption=f"Page {i+1}", use_container_width=True)

st.markdown("---")

# Process button
if st.button("▶️ Extract & Convert to CSV", type="primary",
             use_container_width=True):

    all_dfs   = []
    all_texts = []
    errors    = []

    progress = st.progress(0)
    status   = st.empty()

    for i, f in enumerate(uploaded_pages):
        status.text(f"Reading page {i+1} of {len(uploaded_pages)}: {f.name}…")
        ext  = Path(f.name).suffix.lower()
        mime = MIME_MAP.get(ext, "image/jpeg")

        raw = extract_table_from_image(f.getvalue(), mime, hint)

        if raw.startswith("ERROR:"):
            errors.append(f"Page {i+1} ({f.name}): {raw}")
            progress.progress((i+1) / len(uploaded_pages))
            continue

        csv_text = clean_csv_text(raw)
        all_texts.append((f"Page {i+1}", csv_text))

        df_page = parse_csv_text(csv_text)
        if df_page is not None and not df_page.empty:
            df_page["_source_page"] = i + 1
            all_dfs.append(df_page)
        else:
            errors.append(f"Page {i+1}: Could not parse into table — check raw text below.")

        progress.progress((i+1) / len(uploaded_pages))

    progress.empty()
    status.empty()

    # Show errors
    if errors:
        for e in errors:
            st.warning(f"⚠️ {e}")

    if not all_dfs:
        st.error("Could not extract structured data from any page. Try adding a description hint above.")
        # Show raw extracted text for debugging
        with st.expander("🔍 Raw extracted text (for debugging)"):
            for page_name, text in all_texts:
                st.markdown(f"**{page_name}:**")
                st.code(text)
        st.stop()

    # Merge all pages
    st.markdown("---")
    st.subheader("✅ Extracted Data")

    # Try to merge — align columns across pages
    try:
        merged_df = pd.concat(all_dfs, ignore_index=True)
    except Exception:
        merged_df = all_dfs[0]

    # Drop internal page column for display
    display_df = merged_df.drop(columns=["_source_page"], errors="ignore")

    st.success(f"Extracted **{len(display_df):,} rows** and **{len(display_df.columns)} columns** from {len(all_dfs)} page(s)")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Column editor — let user rename columns
    with st.expander("✏️ Rename or fix columns (optional)"):
        new_names = {}
        cols_grid = st.columns(min(3, len(display_df.columns)))
        for i, col in enumerate(display_df.columns):
            with cols_grid[i % 3]:
                new_name = st.text_input(f"Rename '{col}'", value=col,
                                         key=f"col_rename_{i}")
                new_names[col] = new_name
        if st.button("Apply column names", key="apply_cols"):
            display_df = display_df.rename(columns=new_names)
            st.success("Column names updated.")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Download
    csv_out = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download as CSV",
        data=csv_out,
        file_name="logbook_extracted.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary"
    )

    # Load into main app session
    st.markdown("---")
    st.subheader("🚀 Use this data directly in Sepiru AI")
    if st.button("Load into Sepiru AI for analysis", use_container_width=True):
        st.session_state["df"]       = display_df.copy()
        st.session_state["clean_df"] = display_df.copy()
        st.session_state["filename"] = "logbook_extracted.csv"
        st.session_state["chat_history"] = []
        st.success("✅ Data loaded! Go to the main page to start analyzing.")
        st.balloons()

    # Show raw text per page
    with st.expander("🔍 Raw extracted text per page"):
        for page_name, text in all_texts:
            st.markdown(f"**{page_name}:**")
            st.code(text, language="text")
