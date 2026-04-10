"""
Gemini client — used exclusively for Chat with Data tab.
Google AI Studio free tier: gemini-2.0-flash, 1500 req/day, no credit card.
"""
import os
from typing import Generator


def _get_gemini_key() -> str:
    try:
        import streamlit as st
        k = st.secrets.get("GEMINI_API_KEY", "")
        if k:
            return k
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")


def is_available() -> bool:
    return bool(_get_gemini_key())


def chat(prompt: str, system: str = "",
         model: str = "gemini-2.0-flash") -> Generator[str, None, None]:
    """Stream a response from Gemini. Yields text chunks."""
    key = _get_gemini_key()
    if not key:
        yield "❌ Gemini API key not configured. Add GEMINI_API_KEY to secrets."
        return
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        client = genai.GenerativeModel(model)
        for chunk in client.generate_content(full_prompt, stream=True):
            if chunk.text:
                yield chunk.text
    except ImportError:
        yield "❌ google-generativeai not installed. Add it to requirements.txt."
    except Exception as e:
        yield f"❌ Gemini error: {e}"


def chat_once(prompt: str, system: str = "",
              model: str = "gemini-2.0-flash") -> str:
    """Single-shot generation. Returns full text."""
    return "".join(chat(prompt, system, model))
