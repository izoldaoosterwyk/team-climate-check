"""Known-answer tests for the scoring engine.

Every expected value below was calculated BY HAND first, then encoded here.
Run with:  python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from narrative import grounding_check, template_narrative, build_payload
from scoring import (
    reverse_value,
    respondent_scale_score,
    team_aggregates,
    meets_threshold,
    band_for,
    dispersion_label,
)

# A fixed test scale, independent of instruments.py, so tests stay valid
# even if the instrument items change.
TEST_SCALE = {
    "key": "test",
    "name": "Test scale",
    "scale_min": 1,
    "scale_max": 7,
    "items": [
        {"id": "t1", "reverse": False},
        {"id": "t2", "reverse": True},
        {"id": "t3", "reverse": False},
        {"id": "t4", "reverse": False},
    ],
}


def test_reverse_value():
    # On a 1–7 scale: 1<->7, 2<->6, 4 stays 4.
    assert reverse_value(1, 1, 7) == 7
    assert reverse_value(2, 1, 7) == 6
    assert reverse_value(4, 1, 7) == 4
    # On a 1–5 scale: 2 -> 4.
    assert reverse_value(2, 1, 5) == 4


def test_respondent_score_with_reverse_item():
    # Raw answers: t1=6, t2=2 (reverse -> 6), t3=7, t4=5.
    # Hand calculation: (6 + 6 + 7 + 5) / 4 = 24/4 = 6.0
    answers = {"t1": 6, "t2": 2, "t3": 7, "t4": 5}
    assert respondent_scale_score(answers, TEST_SCALE) == 6.0


def test_respondent_score_missing_item_returns_none():
    assert respondent_scale_score({"t1": 6, "t2": 2, "t3": 7}, TEST_SCALE) is None


def test_respondent_score_out_of_range_returns_none():
    answers = {"t1": 6, "t2": 2, "t3": 9, "t4": 5}
    assert respondent_scale_score(answers, TEST_SCALE) is None


def test_team_aggregates_hand_calculated():
    # Three respondents; hand-scored means: 6.0, 4.0, 5.0.
    #   r1: (6 + rev(2)=6 + 7 + 5)/4 = 6.0
    #   r2: (4 + rev(4)=4 + 4 + 4)/4 = 4.0
    #   r3: (5 + rev(3)=5 + 5 + 5)/4 = 5.0
    # Team mean = 5.0; sample SD of {6,4,5} = 1.0
    responses = [
        {"t1": 6, "t2": 2, "t3": 7, "t4": 5},
        {"t1": 4, "t2": 4, "t3": 4, "t4": 4},
        {"t1": 5, "t2": 3, "t3": 5, "t4": 5},
    ]
    agg = team_aggregates(responses, [TEST_SCALE])["test"]
    assert agg["n"] == 3
    assert agg["mean"] == 5.0
    assert agg["sd"] == 1.0


def test_threshold_gate():
    assert not meets_threshold(3, 4)
    assert meets_threshold(4, 4)
    assert meets_threshold(9, 4)


def test_bands_cover_full_range():
    # Whatever the cut-offs in instruments.py, every possible mean must map
    # to a band and extreme means must map to the extreme bands.
    assert band_for(1.0, TEST_SCALE) == "low"
    assert band_for(7.0, TEST_SCALE) == "high"
    for tenths in range(10, 71):
        assert band_for(tenths / 10, TEST_SCALE) in {"low", "moderate", "high"}


def test_dispersion_labels():
    assert dispersion_label(0.0, TEST_SCALE) == "strongly aligned"
    assert dispersion_label(3.0, TEST_SCALE) == "notably divided"


def test_grounding_check_passes_on_template():
    responses = [
        {"t1": 6, "t2": 2, "t3": 7, "t4": 5},
        {"t1": 4, "t2": 4, "t3": 4, "t4": 4},
        {"t1": 5, "t2": 3, "t3": 5, "t4": 5},
    ]
    agg = team_aggregates(responses, [TEST_SCALE])
    payload = build_payload(agg)
    text = template_narrative(payload)
    passed, offending = grounding_check(text, payload)
    assert passed, f"Template narrative failed grounding: {offending}"


def test_grounding_check_catches_invented_number():
    responses = [
        {"t1": 6, "t2": 2, "t3": 7, "t4": 5},
        {"t1": 4, "t2": 4, "t3": 4, "t4": 4},
        {"t1": 5, "t2": 3, "t3": 5, "t4": 5},
        {"t1": 5, "t2": 3, "t3": 5, "t4": 7},
    ]
    payload = build_payload(team_aggregates(responses, [TEST_SCALE]))
    passed, offending = grounding_check(
        "The team scored 9.4 which is 83 percent above the norm.", payload
    )
    assert not passed
    assert 9.4 in offending
