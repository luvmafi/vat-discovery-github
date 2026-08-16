"""Controlled economics experiment scaffold: dry-run only, no candidate generation or network calls."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a bounded HMRC enumeration feasibility hypothesis; never calls HMRC.")
    parser.add_argument("--approved-candidate-count", type=int, required=True, help="A manually approved, finite list size; ranges are not accepted.")
    parser.add_argument("--requests-per-minute", type=float, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/results/hmrc_experiment_plan.json"))
    args = parser.parse_args()
    if not 1 <= args.approved_candidate_count <= 100 or args.requests_per_minute <= 0:
        raise SystemExit("This scaffold permits only 1–100 manually approved candidates and a positive declared rate.")
    payload = {"status": "PLANNED_DRY_RUN", "live_requests_made": 0, "approved_candidate_count": args.approved_candidate_count,
               "declared_requests_per_minute": args.requests_per_minute, "estimated_elapsed_minutes": args.approved_candidate_count / args.requests_per_minute,
               "timestamp": datetime.now(timezone.utc).isoformat(), "conclusion": "No conclusion: credentials, terms, and explicit approval are required before any live experiment."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
