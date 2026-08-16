"""Selects the ~100-company manual-validation subset from the already-drawn
500-company sample (brief section 22): deterministic, stratified,
proportional to the strata already present in the sample -- not drawn from
companies where VAT is already known, and not cherry-picked.

Uses a seed distinct from the main sample seed so the two draws are
independently reproducible and auditable.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from vat_discovery.sampling.stratify import deterministic_rank, proportional_allocation


def select(sample_csv: Path, target_size: int, seed: int) -> tuple[list[dict], dict]:
    with sample_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    counts = Counter(row["sample_stratum"] for row in rows)
    allocation = proportional_allocation(counts, target_size)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["sample_stratum"]].append(row)

    selected = []
    for stratum, group in grouped.items():
        chosen = sorted(group, key=lambda row: deterministic_rank(row["companies_house_number"], seed))[:allocation[stratum]]
        selected.extend(chosen)

    manifest = {
        "source_sample_csv": str(sample_csv),
        "target_size": target_size,
        "seed": seed,
        "population_strata": len(counts),
        "strata_represented_in_subset": len({row["sample_stratum"] for row in selected}),
        "subset_size": len(selected),
        "subset_unique_companies": len({row["companies_house_number"] for row in selected}),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return selected, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Select the manual-validation subset from the 500-company sample.")
    parser.add_argument("sample_csv", type=Path, default=Path("data/processed/sample.csv"), nargs="?")
    parser.add_argument("output_csv", type=Path, default=Path("data/processed/manual_validation_subset.csv"), nargs="?")
    parser.add_argument("--target-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--manifest", type=Path, default=Path("data/processed/manual_validation_subset_manifest.json"))
    args = parser.parse_args()

    selected, manifest = select(args.sample_csv, args.target_size, args.seed)
    fields = list(selected[0].keys())
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
