# Team Climate Check

Anonymous, validated team check-in on **trust in the leader**, **psychological
safety** and **thriving at work** for team leaders in small firms with no
psychometric training. Scoring is deterministic Python; an LLM (Gemini, via
API) drafts only the narrative section of the report, from team-level
aggregates only.

Built for BUS5033W (AI in IOP) Assignment 2 — Izolda Oosterwyk.

## How it works

| View | URL | Who |
|---|---|---|
| Create a session | `/` | Team leader |
| Anonymous survey | `/?s=CODE` | Team members |
| Report (gated by anonymity threshold) | `/?s=CODE&k=ADMIN_KEY` | Team leader |

No names, emails, IPs or times of day are ever stored. Results are withheld
until the minimum group size (default 4) is reached. The LLM receives
aggregate scores only, and its output is checked against those numbers
(`narrative.grounding_check`) before being shown; on failure the app falls
back to a deterministic template and says so.

## Files

- `app.py` — Streamlit UI and routing
- `instruments.py` — scales, items, anchors, bands, conversation starters (interpretation bands and starters are the owner's editable choices — see header inside)
- `scoring.py` — deterministic scoring (pure Python, unit-tested)
- `storage.py` — Supabase layer
- `narrative.py` — Gemini call, grounding check, template fallback
- `synth.py` — synthetic respondents to known score profiles (validation + demo data)
- `tests/test_scoring.py` — known-answer tests (hand-calculated expected values)
- `supabase_schema.sql` — database setup

## Run it locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then fill it in
streamlit run app.py
```

## Set up the backend (once, ~15 min)

1. **Supabase** — create a free project at supabase.com → SQL Editor → run
   `supabase_schema.sql` → Settings > API: copy the Project URL and the
   **service_role** key into your secrets as `SUPABASE_URL` / `SUPABASE_KEY`.
2. **Gemini** — create a free API key at aistudio.google.com → `GEMINI_API_KEY`.
   Set `GEMINI_MODEL` to a model listed as free on https://ai.google.dev
   (free-tier model names change over time).

## Deploy (Streamlit Community Cloud)

1. Push this folder to a GitHub repo (the `.gitignore` keeps secrets out).
2. share.streamlit.io → New app → pick the repo, main file `app.py`.
3. App Settings > Secrets → paste the contents of your `secrets.toml`,
   and set `APP_BASE_URL` to the app's URL so shareable links render in full.

## Validation

```bash
python -m pytest tests/ -v                      # known-answer tests
python synth.py --profile strained --n 6 --dry-run   # expected scored means
python synth.py --profile strained --n 6 --session CODE  # load a demo session
```

Profiles: `healthy`, `strained`, `divided`. The dry run prints
respondent-level scores and the team mean computed by the same scoring code
the app uses — compare against hand calculations and against the report.
