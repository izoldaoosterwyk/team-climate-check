"""Team Climate Check — main Streamlit app.

Three views, routed by URL query parameters:
  (none)          -> landing page: leader creates a survey session
  ?s=CODE         -> respondent view: anonymous survey
  ?s=CODE&k=KEY   -> leader view: status, and the report once unlocked

Rename the app before Demo Day: change APP_NAME below.
"""

import json

import streamlit as st

import storage
from instruments import SCALES, STARTERS, DEFAULT_MIN_N
from narrative import get_narrative
from scoring import team_aggregates, meets_threshold

APP_NAME = "Team Climate Check"

DB_ERROR = ("The app could not reach its database just now. Please try again "
            "in a minute. (Administrator: check the Supabase secrets.)")

st.set_page_config(page_title=APP_NAME, page_icon="🧭", layout="centered")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_url() -> str:
    """Base URL for building shareable links. Set APP_BASE_URL in secrets
    once deployed; locally the links fall back to query strings."""
    try:
        return st.secrets.get("APP_BASE_URL", "").rstrip("/")
    except Exception:
        return ""


def _link(params: str) -> str:
    base = _base_url()
    return f"{base}/?{params}" if base else f"?{params}  (append to your app URL)"


# ---------------------------------------------------------------------------
# View 1 — landing: create a session
# ---------------------------------------------------------------------------

def landing_view():
    st.title(APP_NAME)
    st.write(
        "Anonymous, validated team check-in on **trust in the leader**, "
        "**psychological safety** and **thriving at work** — scored "
        "automatically, reported in plain language."
    )
    st.subheader("Create a team check-in")
    with st.form("create"):
        team_name = st.text_input("Team name", max_chars=60)
        min_n = st.number_input(
            "Minimum responses before results are shown (anonymity threshold)",
            min_value=3, max_value=15, value=DEFAULT_MIN_N,
            help="No results of any kind are shown below this number. "
                 "This protects respondents in small teams.",
        )
        submitted = st.form_submit_button("Create session")
    if submitted:
        if not team_name.strip():
            st.warning("Please enter a team name.")
            return
        try:
            session = storage.create_session(team_name, min_n)
        except Exception:
            st.error(DB_ERROR)
            return
        st.success("Session created. **Save both links now — the leader link is shown only once.**")
        st.markdown("**Share this link with your team members:**")
        st.code(_link(f"s={session['code']}"))
        st.markdown("**Your private leader link (do not share):**")
        st.code(_link(f"s={session['code']}&k={session['admin_key']}"))


# ---------------------------------------------------------------------------
# View 2 — respondent survey
# ---------------------------------------------------------------------------

def survey_view(session):
    st.title(f"Team check-in: {session['team_name']}")
    st.write(
        "This short survey is **anonymous**. No name, email address or any "
        "other identifier is collected. Your team leader only ever sees "
        f"combined results, and only once at least {session['min_n']} people "
        "have responded. It takes about 5 minutes."
    )

    if st.session_state.get("submitted"):
        st.success("Thank you — your response has been recorded.")
        return

    answers = {}
    with st.form("survey"):
        for scale in SCALES:
            st.subheader(scale["name"])
            st.caption(scale["intro"])
            lo, hi = scale["scale_min"], scale["scale_max"]
            labels = scale["anchor_labels"]
            options = list(range(lo, hi + 1))
            for item in scale["items"]:
                answers[item["id"]] = st.radio(
                    item["text"],
                    options,
                    index=None,
                    horizontal=True,
                    format_func=lambda v, L=labels: f"{v} — {L[v]}" if v in L else str(v),
                    key=item["id"],
                )
            st.divider()
        done = st.form_submit_button("Submit anonymously")

    if done:
        missing = sum(1 for v in answers.values() if v is None)
        if missing:
            st.warning(f"Please answer all items — {missing} still unanswered.")
            return
        try:
            storage.submit_response(session["code"], answers)
        except Exception:
            st.error("Your response could not be saved. Please try submitting again.")
            return
        st.session_state["submitted"] = True
        st.rerun()


# ---------------------------------------------------------------------------
# View 3 — leader dashboard and report
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=3600)
def _cached_narrative(aggregates_json: str):
    return get_narrative(json.loads(aggregates_json))


def leader_view(session):
    st.title(f"Leader view: {session['team_name']}")
    try:
        count = storage.response_count(session["code"])
    except Exception:
        st.error(DB_ERROR)
        return
    min_n = session["min_n"]
    st.metric("Responses received", count)

    if not meets_threshold(count, min_n):
        st.info(
            f"Results unlock at **{min_n} responses** to protect anonymity. "
            f"{min_n - count} more needed."
        )
        st.markdown("**Respondent link to share:**")
        st.code(_link(f"s={session['code']}"))
        return

    responses = storage.fetch_responses(session["code"])
    aggregates = team_aggregates(responses, SCALES)

    st.header("Team results")
    report_md = [f"# {APP_NAME} — {session['team_name']}", f"Responses: {count}", ""]

    for scale in SCALES:
        agg = aggregates[scale["key"]]
        if agg.get("n", 0) == 0:
            continue
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric(agg["name"], f"{agg['mean']} / {agg['scale_max']}")
        with col2:
            st.progress(
                (agg["mean"] - agg["scale_min"]) / (agg["scale_max"] - agg["scale_min"]),
                text=f"{agg['band'].capitalize()} · responses {agg['dispersion']}",
            )
        report_md.append(
            f"## {agg['name']}\n"
            f"Mean {agg['mean']} on a {agg['scale_min']}–{agg['scale_max']} scale "
            f"({agg['band']}); responses {agg['dispersion']} (SD {agg['sd']})."
        )

    st.header("What this means")
    with st.spinner("Drafting the narrative…"):
        # Cached so refreshing the page doesn't re-call the API for the
        # same results (saves free-tier quota and keeps the demo fast).
        narrative, source = _cached_narrative(json.dumps(aggregates, sort_keys=True))
    if source == "ai":
        st.caption(
            "✦ AI-drafted from your team's aggregate scores only, and "
            "automatically checked against them. No individual responses "
            "were shared with the AI."
        )
    else:
        st.caption("Standard narrative (AI drafting unavailable or failed checks).")
    st.write(narrative)
    report_md += ["", "## What this means", narrative, ""]

    st.header("Conversation starters")
    st.caption("Curated suggestions keyed to your results — not AI-generated.")
    for scale in SCALES:
        agg = aggregates[scale["key"]]
        if agg.get("n", 0) == 0:
            continue
        starters = STARTERS.get((scale["key"], agg["band"]), [])
        if starters:
            st.markdown(f"**{agg['name']}**")
            for s in starters:
                st.markdown(f"- {s}")
                report_md.append(f"- ({agg['name']}) {s}")

    st.download_button(
        "Download report (Markdown)",
        "\n".join(report_md),
        file_name=f"team_report_{session['code']}.md",
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def main():
    code = st.query_params.get("s")
    key = st.query_params.get("k")

    if not code:
        landing_view()
        return

    try:
        session = storage.get_session(code)
    except Exception:
        st.error(DB_ERROR)
        return
    if session is None:
        st.error("This session code was not found. Check the link you were sent.")
        return

    if key:
        if key == session["admin_key"]:
            leader_view(session)
        else:
            st.error("Invalid leader key.")
    else:
        survey_view(session)


main()
