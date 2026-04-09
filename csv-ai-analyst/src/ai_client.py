"""
Multi-provider AI client: Gemini (primary/free), Groq, OpenAI, Anthropic, Ollama.
"""

import os
import requests
import json
from typing import Generator
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, fallback: str = "") -> str:
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, fallback)


class AIClient:
    PROVIDERS = ["gemini", "groq", "openai", "anthropic", "ollama"]

    def __init__(self):
        self.provider = _get_secret("AI_PROVIDER", os.getenv("AI_PROVIDER", "gemini")).lower()
        self.temperature = float(os.getenv("TEMPERATURE", 0.3))
        self.max_tokens = int(os.getenv("MAX_TOKENS", 3000))
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=_get_secret("GEMINI_API_KEY"))
                self.model = _get_secret("GEMINI_MODEL", "gemini-1.5-flash")
                self._genai = genai
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                raise ImportError("Run: pip install google-generativeai")

        elif self.provider == "groq":
            try:
                from groq import Groq
                self._client = Groq(api_key=_get_secret("GROQ_API_KEY"))
                self.model = _get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")
            except ImportError:
                raise ImportError("Run: pip install groq")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=_get_secret("OPENAI_API_KEY"))
                self.model = _get_secret("OPENAI_MODEL", "gpt-4o-mini")
            except ImportError:
                raise ImportError("Run: pip install openai")

        elif self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=_get_secret("ANTHROPIC_API_KEY"))
                self.model = _get_secret("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
            except ImportError:
                raise ImportError("Run: pip install anthropic")

        else:
            self.provider = "ollama"
            self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    def check_connection(self) -> tuple[bool, str]:
        try:
            if self.provider == "gemini":
                # Tiny test call
                r = self._client.generate_content("hi")
                from src.quota_guard import increment
                increment(1)
                return True, f"Gemini connected · {self.model}"

            elif self.provider == "ollama":
                r = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models", [])]
                    return True, f"Ollama · {len(models)} model(s)"
                return False, "Ollama error"

            elif self.provider == "groq":
                self._client.models.list()
                return True, f"Groq · {self.model}"

            elif self.provider == "openai":
                self._client.models.list()
                return True, f"OpenAI · {self.model}"

            elif self.provider == "anthropic":
                self._client.messages.create(
                    model=self.model, max_tokens=5,
                    messages=[{"role": "user", "content": "hi"}]
                )
                return True, f"Anthropic · {self.model}"

        except Exception as e:
            return False, str(e)

    def get_available_models(self) -> list[str]:
        if self.provider == "gemini":
            return [self.model]
        if self.provider == "ollama":
            try:
                r = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if r.status_code == 200:
                    return [m["name"] for m in r.json().get("models", [])]
            except Exception:
                pass
            return []
        return [self.model]

    def generate(self, prompt: str, system: str = "") -> str:
        try:
            if self.provider == "gemini":
                return self._gemini_generate(prompt, system)
            elif self.provider == "ollama":
                return self._ollama_generate(prompt, system)
            elif self.provider in ("groq", "openai"):
                return self._openai_style_generate(self._client, prompt, system)
            elif self.provider == "anthropic":
                return self._anthropic_generate(prompt, system)
        except Exception as e:
            return f"❌ Error: {e}"

    def generate_stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        try:
            if self.provider == "gemini":
                yield from self._gemini_stream(prompt, system)
            elif self.provider == "ollama":
                yield from self._ollama_stream(prompt, system)
            elif self.provider in ("groq", "openai"):
                yield from self._openai_style_stream(self._client, prompt, system)
            elif self.provider == "anthropic":
                yield from self._anthropic_stream(prompt, system)
        except Exception as e:
            yield f"❌ Streaming error: {e}"

    # ── Gemini ────────────────────────────────────────────────────────────────
    def _gemini_generate(self, prompt: str, system: str) -> str:
        from src.quota_guard import increment
        full = f"{system}\n\n{prompt}" if system else prompt
        r = self._client.generate_content(full)
        increment(1)
        return r.text

    def _gemini_stream(self, prompt: str, system: str) -> Generator[str, None, None]:
        from src.quota_guard import increment
        full = f"{system}\n\n{prompt}" if system else prompt
        for chunk in self._client.generate_content(full, stream=True):
            if chunk.text:
                yield chunk.text
        increment(1)

    def _ollama_generate(self, prompt: str, system: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["response"]

    def _ollama_stream(self, prompt: str, system: str) -> Generator[str, None, None]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {"temperature": self.temperature},
        }
        with requests.post(f"{self.base_url}/api/generate", json=payload,
                           stream=True, timeout=120) as r:
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line)
                    yield chunk.get("response", "")
                    if chunk.get("done"):
                        break

    def _openai_style_generate(self, client, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content

    def _openai_style_stream(self, client, messages_or_prompt, system: str = "") -> Generator[str, None, None]:
        if isinstance(messages_or_prompt, str):
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": messages_or_prompt})
        else:
            messages = messages_or_prompt
            if system and (not messages or messages[0]["role"] != "system"):
                messages = [{"role": "system", "content": system}] + messages
        stream = client.chat.completions.create(
            model=self.model, messages=messages,
            temperature=self.temperature, max_tokens=self.max_tokens, stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _anthropic_generate(self, prompt: str, system: str) -> str:
        kwargs = dict(
            model=self.model, max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        msg = self._client.messages.create(**kwargs)
        return msg.content[0].text

    def _anthropic_stream(self, prompt: str, system: str) -> Generator[str, None, None]:
        kwargs = dict(
            model=self.model, max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    def generate_stream_messages(self, messages: list, system: str = "") -> Generator[str, None, None]:
        """Stream a response using full message history."""
        try:
            if self.provider == "ollama":
                # Convert to single prompt with history
                prompt = ""
                for m in messages:
                    role = "User" if m["role"] == "user" else "Assistant"
                    prompt += f"\n{role}: {m['content']}"
                prompt += "\nAssistant:"
                yield from self._ollama_stream(prompt, system)

            elif self.provider in ("groq", "openai"):
                msgs = []
                if system:
                    msgs.append({"role": "system", "content": system})
                msgs.extend(messages)
                yield from self._openai_style_stream(self._client, msgs)

            elif self.provider == "anthropic":
                yield from self._anthropic_stream_messages(messages, system)

        except Exception as e:
            yield f"❌ Error: {e}"

    def _anthropic_stream_messages(self, messages: list, system: str = "") -> Generator[str, None, None]:
        kwargs = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
