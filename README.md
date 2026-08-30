# Sepiru AI

400 million people have data — but not the money, language, or tools to
understand it. Sepiru AI changes that.

Sepiru AI is a free, privacy-first, AI-powered data intelligence platform
that transforms any CSV, Excel file, or photograph of a handwritten register
into analyst-grade insights — in 14 languages, with zero login, zero cloud
storage, and zero cost. Powered by Google Gemini 2.0 Flash.

- Live demo: [sepiru-ai.streamlit.app](https://sepiru-ai.streamlit.app/)
- Demo video: [Watch on YouTube](https://youtu.be/_eSoLRVqE8I)


## Table of contents

- Requirements
- Installation
- Configuration
- Features
- Technology stack
- UN SDG alignment
- Privacy and security
- Troubleshooting & FAQ
- Maintainers


## Requirements

- Python 3.10 or higher
- A free [Groq API key](https://console.groq.com) (required)
- A free [Google Gemini API key](https://aistudio.google.com) (optional,
  used for Chat with Data; falls back to Groq if unavailable)
- No database, no cloud infrastructure, no paid services required


## Installation

1. Clone the repository:

```bash
git clone https://github.com/SARazzaq/Sepiru-AI.git
cd Sepiru-AI/csv-ai-analyst
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the `csv-ai-analyst/` directory:

```
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_API_KEY=your_gemini_api_key_here
```

5. Run the application:

```bash
streamlit run app.py
```

6. Open your browser at `http://localhost:8501`


## Configuration

### API keys

All API keys are read from environment variables or Streamlit secrets.
No key is ever hardcoded in the source code.

For local development, add keys to `.env` as shown in the Installation
section. The `.env` file is listed in `.gitignore` and will never be
committed.

For Streamlit Cloud deployment, add secrets via the Streamlit Cloud
dashboard under App Settings → Secrets:

```toml
AI_PROVIDER    = "groq"
GROQ_API_KEY   = "gsk_your_key_here"
GROQ_MODEL     = "llama-3.3-70b-versatile"
GEMINI_API_KEY = "AIza_your_key_here"
```

### AI provider fallback

The platform uses Google Gemini 2.0 Flash as the primary provider for
the Chat with Data feature. If Gemini quota is reached, it automatically
falls back to Groq LLaMA 3.3 70B with a notification to the user.
All other features always use Groq.

### Quota limits

- Groq free tier: 14,400 requests/day (platform stops at 14,000)
- Gemini free tier: 1,500 requests/day (platform stops at 1,400)

The quota guard system monitors usage in session state and displays a
maintenance page with countdown timer when limits are approached.

### Security gate

The landing page presents a custom-coded math CAPTCHA and honeypot bot
trap. No third-party CAPTCHA service is used. No user data is collected
during the security check.


## Features

### Core analytical features

- **Conversational data chat** — ask questions in plain language in any
  of 14 supported languages; powered by Google Gemini 2.0 Flash with
  automatic fallback to Groq LLaMA 3.3 70B
- **ML model training** — auto-detects classification vs regression;
  trains 10+ models including Random Forest, XGBoost, LightGBM, and
  CatBoost with 5-fold cross-validation and model leaderboard
- **Model explainability** — translates every ML prediction into plain
  language in the user's chosen language
- **Anomaly detection** — detects outliers using three independent
  methods (IQR, Z-Score, Isolation Forest) with AI-generated business
  alerts
- **Time-series forecasting** — predicts future values with confidence
  bands using six different methods
- **Natural language to SQL** — converts plain English questions to SQL
  and executes them instantly using DuckDB in-memory engine
- **Multilingual AI** — chat, translate, and analyze data in 14
  languages including Hindi, Arabic, Tamil, Chinese, Spanish, and French
- **Business report generator** — produces executive-ready reports in
  any language with one click
- **Vision AI** — analyzes image datasets with single-image chat and
  batch analysis using Groq LLaMA 4 Scout 17B
- **Logbook digitizer** — photographs handwritten registers and converts
  them to structured CSV via a two-pass AI pipeline

### Data processing features

- **Data profiling** — deep statistical analysis including skewness,
  kurtosis, correlation heatmaps, and distribution grids
- **Data cleaning** — auto-detects and fixes missing values, duplicates,
  outliers, and constant columns
- **3D visualizations** — interactive 3D scatter, surface, correlation
  networks, and custom chart builder using Plotly

### Supported languages

English, Hindi, Spanish, French, German, Arabic, Chinese (Simplified),
Japanese, Portuguese, Russian, Korean, Italian, Dutch, Turkish


## Technology stack

- **Frontend framework** — Streamlit
- **Primary AI** — Google Gemini 2.0 Flash (Chat with Data)
- **Secondary AI** — Groq + LLaMA 3.3 70B (all other features)
- **Vision AI** — Groq + LLaMA 4 Scout 17B (image analysis, OCR)
- **ML engine** — scikit-learn, XGBoost, LightGBM, CatBoost
- **Data processing** — Pandas, NumPy, SciPy
- **SQL engine** — DuckDB (in-memory, zero external transmission)
- **Visualization** — Plotly
- **Deployment** — Streamlit Cloud (free tier, global)
- **Animations** — Pure Canvas API (no Three.js or external libraries)
- **Security** — Custom-coded CAPTCHA and honeypot (no third-party)


## UN SDG alignment

Sepiru AI directly addresses three United Nations Sustainable Development
Goals:

- **SDG 8 — Decent work and economic growth**: empowers small businesses,
  farmers, and NGO workers to make data-driven decisions that improve
  profitability and sustainability
- **SDG 4 — Quality education**: delivers data literacy in 14 languages
  to non-English speakers excluded from the global knowledge economy
- **SDG 10 — Reduced inequalities**: gives a street vendor in Mumbai the
  same analytical power as a Fortune 500 data team, at zero cost


## Privacy and security

Sepiru AI was designed around a privacy-first architecture following
direct feedback from real users who refused cloud-based tools due to
data privacy concerns.

- No user accounts or authentication required
- No Firebase, no Google OAuth, no cloud database of any kind
- All uploaded files are processed in session memory only
- All data is permanently deleted when the browser tab is closed
- No usage logs, no analytics, no user tracking of any kind
- Custom-coded math CAPTCHA with honeypot bot trap
- Input sanitization against prompt injection attacks
- Rate limiting and quota guard system
- All security features built from scratch, zero third-party dependencies


## Troubleshooting & FAQ

**The CAPTCHA is not letting me in even with the correct answer.**
This is caused by browser autofill filling the hidden honeypot field.
Disable autofill for this site or use a private/incognito window.

**The app shows "Under Maintenance".**
The daily API quota has been reached. The app automatically resumes at
midnight UTC. The maintenance page shows the exact countdown timer.

**Chat with Data is showing a Gemini quota error.**
The platform automatically falls back to Groq LLaMA 3.3 70B and
notifies you in the chat. This is expected behavior.

**ML training shows a datetime error.**
Ensure your date columns are in a standard format (YYYY-MM-DD). The
platform converts datetime columns to epoch seconds automatically.

**The Vision AI page says GROQ_API_KEY not set.**
Add your Groq API key to Streamlit Cloud secrets or your local .env
file as described in the Configuration section above.

**The logbook digitizer is not recognizing my handwriting.**
Add a description in the hint field (e.g. "Sales register with date,
item, quantity, price"). This significantly improves accuracy.


## Maintainers

- Sk Abdur Razzaq — [GitHub profile](https://github.com/SARazzaq)

Built for humanity. Free forever.
