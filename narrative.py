"""Narrative generation.

Where the AI sits at run time — and the guardrails around it:
1. The LLM receives ONLY team-level aggregates (means, SDs, n, bands).
   No individual responses, no item-level data, no names. This is the
   POPIA design decision: nothing identifiable ever leaves the app.
2. The LLM only narrates. All scores are computed deterministically in
   scoring.py, and all advice (conversation starters) is curated human
   content from instruments.py. The model is not allowed to coach.
3. Grounding check: after generation, every number in the narrative is
   verified against the numbers that were sent. If an unverifiable number
   appears, the app regenerates once, then falls back to a deterministic
   template. The reader is always told which version they are seeing.
"""

import json
import re
import traceback

# The current free-tier Flash model changes over time — set GEMINI_MODEL in
# secrets to whatever https://ai.google.dev lists as free when you deploy.
DEFAULT_MODEL = "gemini-2.5-flash"

PROMPT_TEMPLATE = """You are drafting the narrative section of a team feedback report
for a team leader in a small South African firm who has no psychometric training.

Team-level survey results (the ONLY data you have):
{payload}

Scales were answered anonymously by team members. "mean" is the team average on the
response scale running from scale_min to scale_max. "sd" is the standard deviation.
"band" and "dispersion" are pre-computed interpretations.

Write 150–220 words of plain British English prose. Rules:
- Describe what the results show, scale by scale, in plain language.
- Use ONLY numbers that appear in the data above. Do not compute, estimate or
  introduce any other number.
- Translate "dispersion" into plain terms (e.g. whether the team sees things
  similarly or views differ).
- Do NOT give advice, action steps, or recommendations — these are provided
  elsewhere in the report by a human.
- Do NOT speculate about causes, individuals, or anyone's state of mind.
- No headings, no bullet points, no preamble — just the prose."""


def build_payload(aggregates: dict) -> dict:
    """The complete data sent to the LLM. Deliberately aggregate-only."""
    return {
        key: agg for key, agg in aggregates.items() if agg.get("n", 0) > 0
    }


def _allowed_numbers(payload: dict) -> set:
    allowed = set()
    for agg in payload.values():
        for field in ("n", "mean", "sd", "scale_min", "scale_max"):
            v = agg.get(field)
            if v is None:
                continue
            allowed.add(round(float(v), 2))
            allowed.add(round(float(v), 1))
            allowed.add(float(int(v)))
    return allowed


def grounding_check(text: str, payload: dict):
    """Return (passed, offending_numbers). A number 'passes' if it matches a
    number in the payload within rounding tolerance."""
    allowed = _allowed_numbers(payload)
    found = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    offending = [
        x for x in found
        if not any(abs(x - a) <= 0.051 for a in allowed)
    ]
    return (len(offending) == 0, offending)


def template_narrative(payload: dict) -> str:
    """Deterministic fallback — no AI involved."""
    parts = []
    for agg in payload.values():
        parts.append(
            f"{agg['name']}: the team average is {agg['mean']} on a "
            f"{agg['scale_min']}-to-{agg['scale_max']} scale ({agg['band']}), "
            f"based on {agg['n']} responses. Responses were {agg['dispersion']} "
            f"(SD {agg['sd']})."
        )
    return " ".join(parts)


def _call_gemini(prompt: str) -> str:
    from google import genai
    from storage import _get_secret

    client = genai.Client(api_key=_get_secret("GEMINI_API_KEY"))
    try:
        model = _get_secret("GEMINI_MODEL")
    except RuntimeError:
        model = DEFAULT_MODEL
    response = client.models.generate_content(model=model, contents=prompt)
    return (response.text or "").strip()


def get_narrative(aggregates: dict):
    """Returns (text, source) where source is 'ai' or 'template'.

    Tries the LLM, verifies grounding, retries once on failure, then falls
    back to the deterministic template. Any API error also falls back.
    """
    payload = build_payload(aggregates)
    prompt = PROMPT_TEMPLATE.format(payload=json.dumps(payload, indent=2))
    for attempt in range(2):
        try:
            text = _call_gemini(prompt)
        except Exception:
            # Logged server-side only; the reader sees the labelled fallback.
            traceback.print_exc()
            break
        if text:
            passed, offending = grounding_check(text, payload)
            if passed:
                return text, "ai"
            # One stricter retry naming the offending numbers.
            prompt += (
                f"\n\nYour previous draft contained numbers not present in the "
                f"data ({offending}). Rewrite it using only numbers from the data."
            )
    return template_narrative(payload), "template"
