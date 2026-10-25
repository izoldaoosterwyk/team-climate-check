"""Instrument configuration — the psychometric content of the tool.

EVERYTHING the app measures and says is driven by this file. The code is
item-count agnostic: add or remove items freely and scoring adjusts.

>>> STILL TO DO (Grant) <<<
1. Review BANDS and DISPERSION cut-offs — interpretive choices you must
   be able to defend (your dissertation sample's descriptives are a
   defensible basis). The defaults below are placeholders.
2. Rewrite the conversation starters in STARTERS in your own words.

Items, 6-point response scale and reverse-scoring entered as administered
in the dissertation questionnaire (confirmed 12 Oct 2026). A virtuous
leadership scale (Ou Yang, 2021, 28 items) was considered and dropped to
stay with the three constructs in the project proposal and keep the survey
short — document this decision in the outline's Design phases section.
"""

SCALES = [
    {
        "key": "trust",
        "name": "Trust in the leader",
        "source": "Ferres & Travaglione (2003), Workplace Trust Survey — trust-in-leader subscale",
        "intro": "The statements below are about your direct team leader. "
                 "Answer honestly — responses are anonymous and your leader "
                 "only ever sees combined team results.",
        "scale_min": 1,
        "scale_max": 6,
        "anchor_labels": {
            1: "Strongly Disagree", 2: "Disagree", 3: "Slightly Disagree",
            4: "Slightly Agree", 5: "Agree", 6: "Strongly Agree",
        },
        "items": [
            # No reverse-scored items (confirmed).
            {"id": "trust_1", "text": "I can rely on my line manager/supervisor when it really matters.", "reverse": False},
            {"id": "trust_2", "text": "My line manager/supervisor keeps their word.", "reverse": False},
            {"id": "trust_3", "text": "My line manager/supervisor has the skills and competence needed to lead effectively.", "reverse": False},
            {"id": "trust_4", "text": "My line manager/supervisor makes decisions that consider my best interests.", "reverse": False},
            {"id": "trust_5", "text": "My line manager/supervisor would support me if I encountered difficulties at work.", "reverse": False},
            {"id": "trust_6", "text": "My line manager/supervisor is honest in dealing with me.", "reverse": False},
            {"id": "trust_7", "text": "My line manager/supervisor treats me in a way that makes me feel confident in them.", "reverse": False},
            {"id": "trust_8", "text": "I trust my line manager/supervisor.", "reverse": False},
        ],
    },
    {
        "key": "safety",
        "name": "Psychological safety",
        "source": "Edmondson (1999)",
        "intro": "The statements below are about working with your line manager/supervisor.",
        "scale_min": 1,
        "scale_max": 6,
        "anchor_labels": {
            1: "Strongly Disagree", 2: "Disagree", 3: "Slightly Disagree",
            4: "Slightly Agree", 5: "Agree", 6: "Strongly Agree",
        },
        "items": [
            # Leader-referent adaptation: all items positively worded, so no
            # reverse scoring (unlike the original Edmondson scale) — confirmed.
            {"id": "safety_1", "text": "If I make a mistake, my line manager/supervisor will not hold it against me.", "reverse": False},
            {"id": "safety_2", "text": "I am able to bring up problems and difficult issues with my line manager/supervisor without feeling that they will penalise or punish me.", "reverse": False},
            {"id": "safety_3", "text": "I feel comfortable being myself when interacting with my line manager/supervisor.", "reverse": False},
            {"id": "safety_4", "text": "I feel safe being open and honest with my manager/supervisor, even when I'm uncertain.", "reverse": False},
            {"id": "safety_5", "text": "It is easy for me to ask my manager/supervisor for help.", "reverse": False},
            {"id": "safety_6", "text": "I can express a different opinion to my manager/supervisor without fear of negative consequences.", "reverse": False},
            {"id": "safety_7", "text": "When working with my manager/supervisor, my unique skills and talents are valued and used.", "reverse": False},
        ],
    },
    {
        "key": "thriving",
        "name": "Thriving at work",
        "source": "Porath et al. (2012), Thriving at Work scale (Vitality + Learning)",
        "intro": "The statements below are about your own experience at work recently.",
        "scale_min": 1,
        "scale_max": 6,
        "anchor_labels": {
            1: "Strongly Disagree", 2: "Disagree", 3: "Slightly Disagree",
            4: "Slightly Agree", 5: "Agree", 6: "Strongly Agree",
        },
        "items": [
            # Vitality subscale (items 1–5); items 3 and 9 reverse-scored.
            {"id": "thriving_1",  "text": "I feel alive and vital.", "reverse": False},
            {"id": "thriving_2",  "text": "I have energy and spirit.", "reverse": False},
            {"id": "thriving_3",  "text": "I do not feel very energetic.", "reverse": True},
            {"id": "thriving_4",  "text": "I feel alert and awake.", "reverse": False},
            {"id": "thriving_5",  "text": "I am looking forward to each new day.", "reverse": False},
            # Learning subscale (items 6–10).
            {"id": "thriving_6",  "text": "I find myself learning often.", "reverse": False},
            {"id": "thriving_7",  "text": "I continue to learn more as time goes by.", "reverse": False},
            {"id": "thriving_8",  "text": "I see myself continually improving.", "reverse": False},
            {"id": "thriving_9",  "text": "I am not learning.", "reverse": True},
            {"id": "thriving_10", "text": "I have developed a lot as a person.", "reverse": False},
        ],
    },
]

# ---------------------------------------------------------------------------
# Interpretation bands — position of the team mean within the anchor range,
# expressed as a fraction of the range: pos = (mean - min) / (max - min).
# PLACEHOLDER cut-offs: justify or replace (e.g. from dissertation norms).
# ---------------------------------------------------------------------------
BANDS = [
    (0.45, "low"),        # pos < 0.45
    (0.70, "moderate"),   # 0.45 <= pos < 0.70
    (1.01, "high"),       # pos >= 0.70
]

# Dispersion labels — SD as a fraction of the anchor range.
# PLACEHOLDER cut-offs: justify or replace.
DISPERSION = [
    (0.12, "strongly aligned"),
    (0.22, "broadly aligned, with some variation"),
    (9.99, "notably divided"),
]

# ---------------------------------------------------------------------------
# Conversation starters — deterministic, curated by YOU, keyed by
# (scale key, band). A deliberate design decision: the LLM narrates the
# numbers; it does not generate advice. Rewrite these in your own words.
# ---------------------------------------------------------------------------
STARTERS = {
    ("trust", "low"): [
        "In the next one-on-ones, ask: 'What is one thing I could do differently that would make it easier to bring problems to me?'",
        "Pick one recent decision you made without explaining the reasoning, and walk the team through it.",
    ],
    ("trust", "moderate"): [
        "Ask the team: 'Where do you feel I follow through well, and where do I drop things?'",
    ],
    ("trust", "high"): [
        "Name what is working: ask the team what they would not want you to change.",
    ],
    ("safety", "low"): [
        "At the next team meeting, share a mistake of your own and what you learned — before asking anything of the team.",
        "Ask: 'What is something we all know but never say in meetings?'",
    ],
    ("safety", "moderate"): [
        "Ask: 'When was the last time someone disagreed with me openly — and what happened next?'",
    ],
    ("safety", "high"): [
        "Protect it: ask the team which habits make it safe to speak up here, so they survive new joiners and pressure.",
    ],
    ("thriving", "low"): [
        "Ask each person: 'What part of your week gives you energy, and what drains it?' Look for one drain you can remove.",
    ],
    ("thriving", "moderate"): [
        "Ask: 'What would you like to be learning that your current work doesn't give you?'",
    ],
    ("thriving", "high"): [
        "Ask what conditions are enabling people to grow, and how to keep them as workload shifts.",
    ],
}

# Default minimum number of responses before any results are shown.
# In line with anonymity thresholds used by commercial survey platforms.
DEFAULT_MIN_N = 4
