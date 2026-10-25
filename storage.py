"""Supabase storage layer.

Design notes (for the project outline):
- Anonymity by design: responses are stored with NO identifier of any kind —
  no name, email, IP, device or browser fingerprint. Only the answers and a
  submission DATE (not time of day, which could identify who was at their
  desk when).
- The database has Row Level Security enabled with no public policies, so it
  is closed to anyone without the service key, which lives only in Streamlit
  Cloud's server-side secrets.
"""

import os
import secrets as pysecrets


def _get_secret(name: str) -> str:
    """Read a secret from Streamlit secrets (deployed app) or the
    environment (synth.py / local scripts)."""
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing secret {name}. Set it in .streamlit/secrets.toml "
            f"or as an environment variable."
        )
    return value


def _client():
    from supabase import create_client
    return create_client(_get_secret("SUPABASE_URL"), _get_secret("SUPABASE_KEY"))


def create_session(team_name: str, min_n: int) -> dict:
    """Create a survey session; returns its code and the leader's admin key."""
    session = {
        "code": pysecrets.token_hex(3),          # e.g. 'a3f9c1'
        "admin_key": pysecrets.token_urlsafe(8), # shown once to the leader
        "team_name": team_name.strip(),
        "min_n": int(min_n),
    }
    _client().table("sessions").insert(session).execute()
    return session


def get_session(code: str):
    """Fetch a session by code; returns None if it does not exist."""
    res = _client().table("sessions").select("*").eq("code", code).execute()
    return res.data[0] if res.data else None


def submit_response(code: str, answers: dict) -> None:
    """Store one anonymous response."""
    _client().table("responses").insert(
        {"session_code": code, "answers": answers}
    ).execute()


def fetch_responses(code: str) -> list:
    """All answer dicts for a session (no other fields are retrieved)."""
    res = _client().table("responses").select("answers").eq(
        "session_code", code
    ).execute()
    return [row["answers"] for row in res.data]


def response_count(code: str) -> int:
    res = _client().table("responses").select(
        "id", count="exact"
    ).eq("session_code", code).execute()
    return res.count or 0
