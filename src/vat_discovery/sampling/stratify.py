"""Deterministic, proportional sample allocation. Does not fetch Companies House data."""
from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

AGE_BUCKETS = ((2, "0_2"), (5, "3_5"), (10, "6_10"), (20, "11_20"))


def age_bucket(incorporation_date: date | None, reference_date: date) -> str | None:
    if incorporation_date is None or incorporation_date > reference_date:
        return None
    years = reference_date.year - incorporation_date.year - ((reference_date.month, reference_date.day) < (incorporation_date.month, incorporation_date.day))
    return next((label for maximum, label in AGE_BUCKETS if years <= maximum), "21_PLUS")


def industry_category(sic_codes: list[str], mapping: dict[str, list[str]]) -> str:
    prefixes = {code.strip()[:2] for code in sic_codes if code.strip()}
    return next((category for category, values in mapping.items() if prefixes.intersection(values)), "Other")


def proportional_allocation(counts: Counter[str], target_size: int) -> dict[str, int]:
    total = sum(counts.values())
    if target_size < 1 or target_size > total:
        raise ValueError("target_size must be between 1 and the population size")
    ideals = {key: target_size * count / total for key, count in counts.items()}
    allocation = {key: int(value) for key, value in ideals.items()}
    remaining = target_size - sum(allocation.values())
    # Stable alphabetical tie-break keeps repeated runs and audit explanations deterministic.
    for key in sorted(counts, key=lambda key: (-(ideals[key] - allocation[key]), key))[:remaining]:
        allocation[key] += 1
    return allocation


def deterministic_rank(company_number: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{company_number}".encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a deterministic proportional sample from a local Companies House export.")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--target-size", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--reference-date", type=date.fromisoformat, default=date(2026, 8, 1))
    parser.add_argument("--mapping", type=Path, default=Path("config/industry_mapping.yaml"))
    args = parser.parse_args()
    import yaml
    mapping = yaml.safe_load(args.mapping.read_text(encoding="utf-8"))
    with args.input_csv.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("company_status", "").upper() == "ACTIVE"]
    if not rows:
        raise SystemExit("No ACTIVE companies were supplied")
    for row in rows:
        inc = date.fromisoformat(row["incorporation_date"]) if row.get("incorporation_date") else None
        category = industry_category(row.get("sic_codes", "").split(";"), mapping)
        bucket = age_bucket(inc, args.reference_date) or "UNKNOWN_AGE"
        row["sample_stratum"] = f"{category}|{bucket}"
    counts = Counter(row["sample_stratum"] for row in rows)
    allocation = proportional_allocation(counts, args.target_size)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["sample_stratum"]].append(row)
    selected = []
    for stratum, group in grouped.items():
        chosen = sorted(group, key=lambda row: deterministic_rank(row["companies_house_number"], args.seed))[:allocation[stratum]]
        for row in chosen:
            row["population_count_in_stratum"] = counts[stratum]
            row["sample_count_in_stratum"] = allocation[stratum]
            row["sample_weight"] = counts[stratum] / allocation[stratum]
        selected.extend(chosen)
    fields = list(rows[0]) + ["population_count_in_stratum", "sample_count_in_stratum", "sample_weight"]
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected)


if __name__ == "__main__":
    main()
