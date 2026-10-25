"""Synthetic respondent generator — the validation workhorse.

Generates anonymous respondents whose item answers produce KNOWN team score
profiles, so the app's output can be checked against hand calculations.
No real employee data is ever used.

Usage:
  python synth.py --profile healthy --n 8 --dry-run
      Print the generated responses and their expected scored means
      (hand-check these against the app's report).

  python synth.py --profile strained --n 6 --session a3f9c1
      Submit the generated responses to a live session (requires
      SUPABASE_URL and SUPABASE_KEY in the environment).

Profiles (targets are positions within each scale's range, 0–1):
  healthy   — high on all three scales, aligned
  strained  — low safety, moderate trust, low thriving
  divided   — moderate means but high spread (the team disagrees)
"""

import argparse
import json
import random

from instruments import SCALES
from scoring import respondent_scale_score, reverse_value

PROFILES = {
    "healthy":  {"trust": (0.85, 0.05), "safety": (0.80, 0.05), "thriving": (0.80, 0.05)},
    "strained": {"trust": (0.55, 0.08), "safety": (0.30, 0.08), "thriving": (0.35, 0.08)},
    "divided":  {"trust": (0.55, 0.25), "safety": (0.50, 0.28), "thriving": (0.55, 0.25)},
}


def generate_respondent(profile: dict, rng: random.Random) -> dict:
    """One respondent's raw answers (as they would be stored), built so that
    the SCORED values land near the profile targets."""
    answers = {}
    for scale in SCALES:
        lo, hi = scale["scale_min"], scale["scale_max"]
        target_pos, sd_pos = profile[scale["key"]]
        # The respondent's underlying standing on the construct:
        latent = lo + target_pos * (hi - lo) + rng.gauss(0, sd_pos * (hi - lo))
        for item in scale["items"]:
            value = round(latent + rng.gauss(0, 0.5))
            value = max(lo, min(hi, value))
            # Store the RAW answer: for reverse-worded items the raw answer
            # is the mirror of the construct level, so that scoring.py's
            # reverse-scoring recovers it.
            if item["reverse"]:
                value = int(reverse_value(value, lo, hi))
            answers[item["id"]] = value
    return answers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--n", type=int, default=8)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--session", help="Session code to submit to")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    respondents = [
        generate_respondent(PROFILES[args.profile], rng) for _ in range(args.n)
    ]

    # Expected scored means — compute with the same scoring code the app
    # uses, and print respondent-level scores for hand-checking.
    print(f"Profile '{args.profile}', n={args.n}, seed={args.seed}\n")
    for scale in SCALES:
        scores = [respondent_scale_score(r, scale) for r in respondents]
        team_mean = sum(scores) / len(scores)
        print(f"{scale['name']}: respondent scores "
              f"{[round(s, 2) for s in scores]} -> team mean {team_mean:.2f}")

    if args.dry_run or not args.session:
        print("\nDry run — nothing submitted. First respondent's raw answers:")
        print(json.dumps(respondents[0], indent=2))
        return

    import storage
    for r in respondents:
        storage.submit_response(args.session, r)
    print(f"\nSubmitted {args.n} synthetic responses to session {args.session}.")


if __name__ == "__main__":
    main()
