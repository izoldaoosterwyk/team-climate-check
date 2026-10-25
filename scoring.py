"""Deterministic scoring. Pure Python, no AI, no external dependencies.

Every number the tool reports is produced here and is unit-tested against
hand-calculated values in tests/test_scoring.py.
"""

from statistics import mean, stdev

from instruments import BANDS, DISPERSION


def reverse_value(value: float, scale_min: int, scale_max: int) -> float:
    """Reverse-score a single item response (e.g. on 1–7, a 2 becomes a 6)."""
    return scale_min + scale_max - value


def respondent_scale_score(answers: dict, scale: dict):
    """Mean of a respondent's items for one scale, after reverse-scoring.

    `answers` maps item id -> raw response. Returns None if any item of the
    scale is missing or out of range (the survey UI enforces completeness;
    this guards data arriving by any other route, e.g. synthetic data bugs).
    """
    values = []
    for item in scale["items"]:
        raw = answers.get(item["id"])
        if raw is None:
            return None
        raw = float(raw)
        if not (scale["scale_min"] <= raw <= scale["scale_max"]):
            return None
        if item["reverse"]:
            raw = reverse_value(raw, scale["scale_min"], scale["scale_max"])
        values.append(raw)
    return mean(values)


def band_for(scale_mean: float, scale: dict) -> str:
    """Interpretation band for a team mean, by position within the range."""
    rng = scale["scale_max"] - scale["scale_min"]
    pos = (scale_mean - scale["scale_min"]) / rng
    for upper, label in BANDS:
        if pos < upper:
            return label
    return BANDS[-1][1]


def dispersion_label(sd: float, scale: dict) -> str:
    """Plain-language label for how spread out responses are."""
    rng = scale["scale_max"] - scale["scale_min"]
    frac = sd / rng
    for upper, label in DISPERSION:
        if frac < upper:
            return label
    return DISPERSION[-1][1]


def team_aggregates(responses: list, scales: list) -> dict:
    """Team-level aggregates per scale.

    `responses` is a list of answer dicts (one per respondent).
    Only these aggregates ever leave the app (e.g. to the LLM): no
    individual-level or item-level data is exposed anywhere downstream.
    """
    out = {}
    for scale in scales:
        person_scores = [
            s for s in (respondent_scale_score(r, scale) for r in responses)
            if s is not None
        ]
        n = len(person_scores)
        if n == 0:
            out[scale["key"]] = {"n": 0}
            continue
        m = mean(person_scores)
        sd = stdev(person_scores) if n > 1 else 0.0
        out[scale["key"]] = {
            "name": scale["name"],
            "n": n,
            "mean": round(m, 2),
            "sd": round(sd, 2),
            "scale_min": scale["scale_min"],
            "scale_max": scale["scale_max"],
            "band": band_for(m, scale),
            "dispersion": dispersion_label(sd, scale),
        }
    return out


def meets_threshold(n_responses: int, min_n: int) -> bool:
    """Anonymity gate: no results of any kind below the minimum group size."""
    return n_responses >= min_n
