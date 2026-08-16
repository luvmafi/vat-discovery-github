"""Loads the sampler's output CSV (see sampling.stratify) into the local SQLite
database's ``companies`` and ``sample`` tables. Read-only with respect to the
CSV; never fetches anything."""
from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from vat_discovery.normalization.address import normalize_address
from vat_discovery.normalization.company import normalize_company_name
from vat_discovery.sampling.stratify import age_bucket


def load(sample_csv: Path, db_path: Path, sample_seed: int) -> int:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    sampled_at = datetime.now(timezone.utc).isoformat()
    loaded = 0
    with sample_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            incorporation = row.get("incorporation_date") or None
            sic_codes = row.get("sic_codes", "")
            industry_category = row["sample_stratum"].split("|", 1)[0]
            inc_date = date.fromisoformat(incorporation) if incorporation else None
            company_age = None
            if inc_date is not None:
                today = date.today()
                company_age = today.year - inc_date.year - ((today.month, today.day) < (inc_date.month, inc_date.day))
            cursor = connection.execute(
                """INSERT INTO companies
                   (companies_house_number, raw_company_name, normalized_company_name, company_status,
                    raw_address, normalized_address, postcode, sic_codes, industry_category, incorporation_date, company_age_years)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(companies_house_number) DO NOTHING""",
                (
                    row["companies_house_number"],
                    row["raw_company_name"],
                    normalize_company_name(row["raw_company_name"]),
                    row["company_status"],
                    row.get("raw_address") or None,
                    normalize_address(row.get("raw_address")),
                    row.get("postcode") or None,
                    sic_codes,
                    industry_category,
                    incorporation,
                    company_age,
                ),
            )
            if cursor.rowcount == 0:
                continue
            company_id = cursor.lastrowid
            connection.execute(
                """INSERT INTO sample
                   (company_id, stratum, sampled_at, sample_seed, population_count_in_stratum, sample_count_in_stratum, sample_weight)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    company_id,
                    row["sample_stratum"],
                    sampled_at,
                    sample_seed,
                    int(row["population_count_in_stratum"]),
                    int(row["sample_count_in_stratum"]),
                    float(row["sample_weight"]),
                ),
            )
            loaded += 1
    connection.commit()
    connection.close()
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Load a generated sample CSV into the local SQLite database.")
    parser.add_argument("sample_csv", type=Path)
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    parser.add_argument("--sample-seed", type=int, default=20260815)
    args = parser.parse_args()
    loaded = load(args.sample_csv, args.db, args.sample_seed)
    print(f"Loaded {loaded} companies into {args.db}")


if __name__ == "__main__":
    main()
