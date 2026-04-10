"""
Explainability Layer — AI explains ML model decisions in plain English.
"""
import streamlit as st
import pandas as pd
import numpy as np

from src.ui_components import load_all_styles
from src.quota_guard import can_proceed, get_usage, reset_time_utc

load_all_styles("assets")

from src.auth import require_auth
require_auth()

from src.ai_client import AIClient

st.markdown("""
<div class='app-header'>
    <h1>🔍 Model <span>Explainability</span></h1>
    <p>Understand why your ML model made each prediction</p>
</div>""", unsafe_allow_html=True)

if not can_proceed():
    st.error(f"⏳ Daily AI quota reached. Resets in **{reset_time_utc()}**.")
    st.stop()

if st.session_state.get("df") is None:
    st.warning("Upload a file on the main page first.")
    st.stop()

if "ml_results" not in st.session_state:
    st.info("Train a model on the ML Training page first, then come back here.")
    st.stop()

results = st.session_state["ml_results"]
df = st.session_state.clean_df
u = get_usage()
st.caption(f"AI quota: {u['count']}/{u['limit']} used · {u['remaining']} remaining")

st.subheader("🧠 Model Overview")
c1, c2, c3 = st.columns(3)
c1.metric("Model", results["model_name"])
c2.metric("Task", results["task"].capitalize())
if results["task"] == "classification":
    c3.metric("Accuracy", f"{results['accuracy']}%")
else:
    c3.metric("R²", results["r2"])

if results.get("fi_fig"):
    st.plotly_chart(results["fi_fig"], use_container_width=True)

st.markdown("---")
st.subheader("💬 Ask the Model to Explain Itself")

lang = st.selectbox("Response language", [
    "English","Hindi","Spanish","French","German","Arabic","Chinese","Portuguese"
])

questions = [
    "Why did the model make these predictions?",
    "Which features matter most and why?",
    "Where is the model likely to be wrong?",
    "Explain this model to a non-technical manager.",
    "What data would improve this model?",
]
q = st.selectbox("Choose a question or type your own", ["Custom…"] + questions)
if q == "Custom…":
    q = st.text_input("Your question")

if st.button("▶️ Explain", type="primary", use_container_width=True) and q:
    if not can_proceed():
        st.error(f"Quota exhausted. Resets in {reset_time_utc()}.")
        st.stop()
    with st.spinner("Generating explanation…"):
        try:
            ai = AIClient()
            if results["task"] == "classification":
                perf = f"Accuracy: {results['accuracy']}%, CV: {results['cv_mean']}%±{results['cv_std']}%"
            else:
                perf = f"MAE:{results['mae']}, RMSE:{results['rmse']}, R²:{results['r2']}"

            feat_imp = ""
            if results.get("feature_importances") is not None:
                fi = results["feature_importances"]
                top = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:8]
                feat_imp = ", ".join(f"{k}({v:.3f})" for k, v in top)

            prompt = f"""ML Model: {results['model_name']}
Task: {results['task']}
Performance: {perf}
Top features: {feat_imp or 'not available'}
Dataset columns: {list(df.columns)}

Question: {q}
Answer in {lang}. Be specific with feature names and numbers."""

            answer = ai.generate(prompt, system="You are an ML explainability expert.")
            st.markdown(f'<div class="insight-box">{answer}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")
