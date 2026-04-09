"""
Quota Guard — tracks daily Gemini API usage.
Gemini free tier: 1,500 requests/day, resets at midnight UTC.
We stop at DAILY_LIMIT to keep a safety buffer.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Groq free tier: 14,400 req/day — stop at 14,000 to keep 400 buffer
DAILY_LIMIT = 14000
_STORE = Path(__file__).parent.parent / ".quota_state.json"


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load() -> dict:
    try:
        if _STORE.exists():
            data = json.loads(_STORE.read_text())
            # Reset if it's a new day
            if data.get("date") != _today_utc():
                return {"date": _today_utc(), "count": 0}
            return data
    except Exception:
        pass
    return {"date": _today_utc(), "count": 0}


def _save(data: dict):
    try:
        _STORE.write_text(json.dumps(data))
    except Exception:
        pass


def get_usage() -> dict:
    """Returns {date, count, remaining, pct_used, limit}."""
    d = _load()
    remaining = max(0, DAILY_LIMIT - d["count"])
    return {
        "date":      d["date"],
        "count":     d["count"],
        "remaining": remaining,
        "limit":     DAILY_LIMIT,
        "pct_used":  round(d["count"] / DAILY_LIMIT * 100, 1),
        "exhausted": remaining == 0,
    }


def increment(n: int = 1):
    """Call after each successful API request."""
    d = _load()
    d["count"] = d.get("count", 0) + n
    _save(d)


def can_proceed() -> bool:
    """Returns False when daily quota is exhausted."""
    return get_usage()["remaining"] > 0


def reset_time_utc() -> str:
    """Human-readable time until quota resets (midnight UTC)."""
    now = datetime.now(timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    next_midnight = midnight + timedelta(days=1)
    delta = next_midnight - now
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m = rem // 60
    return f"{h}h {m}m"
