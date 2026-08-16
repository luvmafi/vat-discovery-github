"""Records reviews of the 100-company manual-validation subset
(data/processed/manual_validation_subset.csv, see brief section 22) into the
`manual_reviews` table.

IMPORTANT LABELLING NOTE: the brief specifies independent *human* manual
review, precisely so it can catch failure modes the automated pipeline
cannot see (including, as it turned out, search-summary hallucination --
see docs/findings.md Phase 2 round 3). These reviews were performed by the
operating agent using the same web-search/fetch tools as the Phase 2 pilots,
at the user's explicit request, not by an independent human reviewer.
`reviewer` is recorded as `AGENT_ASSISTED_NOT_INDEPENDENT_HUMAN_REVIEW` in
every row so this is never later misread as satisfying the brief's original
manual-validation requirement -- it is a related but distinct check.

Run in batches (`--batch-file`) since 100 rigorous per-company checks cannot
responsibly happen in one pass; each batch is a separate, dated JSON file of
observations.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

REVIEWER = "AGENT_ASSISTED_NOT_INDEPENDENT_HUMAN_REVIEW"


def record_batch(db_path: Path, batch_file: Path) -> dict[str, object]:
    observations = json.loads(batch_file.read_text(encoding="utf-8"))
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    reviewed_at = datetime.now(timezone.utc).isoformat()

    inserted = 0
    for obs in observations:
        company_id_row = connection.execute(
            "SELECT company_id FROM companies WHERE companies_house_number = ?",
            (obs["companies_house_number"],),
        ).fetchone()
        if company_id_row is None:
            raise SystemExit(f"Company {obs['companies_house_number']} not found -- load the sample first.")
        connection.execute(
            """INSERT INTO manual_reviews
               (company_id, candidate_id, reviewer, reviewed_at, public_vat_evidence_found,
                manually_identified_vat, evidence_url, evidence_type, confidence, decision, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                company_id_row[0], obs.get("candidate_id"), REVIEWER, reviewed_at,
                int(obs["public_vat_evidence_found"]), obs.get("manually_identified_vat"),
                obs.get("evidence_url"), obs.get("evidence_type"), obs.get("confidence"),
                obs.get("decision"), obs.get("notes"),
            ),
        )
        inserted += 1
    connection.commit()
    connection.close()
    return {"batch_file": str(batch_file), "reviews_inserted": inserted, "reviewed_at": reviewed_at}


def main() -> None:
    parser = argparse.ArgumentParser(description="Record one batch of manual-validation-subset reviews.")
    parser.add_argument("batch_file", type=Path)
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    args = parser.parse_args()
    print(json.dumps(record_batch(args.db, args.batch_file), indent=2))


if __name__ == "__main__":
    main()
