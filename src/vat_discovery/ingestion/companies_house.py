"""Converts a locally downloaded Companies House "Basic Company Data" snapshot
into the population CSV consumed by ``vat_discovery.sampling.stratify``.

Acquisition method (documented, not automated here): Companies House publishes a
free monthly bulk snapshot of live company records as CSV at
https://download.companieshouse.gov.uk/en_output.html (~470MB single file, or
seven smaller parts). It is explicitly "provided free of charge and will not be
supported" by Companies House; the registrar has stated the Free Company Data
Product carries no reuse restrictions as it is public statutory information
(Companies Act 2006), though this is not a formal Open Government Licence
grant. This module deliberately does not fetch that file: it is hundreds of
megabytes, changes monthly, and downloading it is a one-off manual step a
human should perform and record, not something this pipeline does silently.

Expected source header (subset used here): CompanyName, CompanyNumber,
CompanyStatus, RegAddress.AddressLine1, RegAddress.AddressLine2,
RegAddress.PostTown, RegAddress.County, RegAddress.Country,
RegAddress.PostCode, IncorporationDate (DD/MM/YYYY),
SICCode.SicText_1..SICCode.SicText_4 (each "12345 - description" or
"None Supplied").
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

SIC_TEXT_FIELDS = ("SICCode.SicText_1", "SICCode.SicText_2", "SICCode.SicText_3", "SICCode.SicText_4")
ADDRESS_FIELDS = (
    "RegAddress.AddressLine1",
    "RegAddress.AddressLine2",
    "RegAddress.PostTown",
    "RegAddress.County",
    "RegAddress.Country",
)
OUTPUT_FIELDS = (
    "companies_house_number",
    "raw_company_name",
    "company_status",
    "sic_codes",
    "incorporation_date",
    "raw_address",
    "postcode",
)


def parse_sic_codes(row: dict[str, str]) -> list[str]:
    codes = []
    for field in SIC_TEXT_FIELDS:
        text = (row.get(field) or "").strip()
        if not text or text.lower() == "none supplied":
            continue
        code = text.split(" - ", 1)[0].strip()
        if code:
            codes.append(code)
    return codes


def parse_incorporation_date(value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return ""


def convert_row(row: dict[str, str]) -> dict[str, str] | None:
    company_number = (row.get("CompanyNumber") or "").strip()
    company_name = (row.get("CompanyName") or "").strip()
    if not company_number or not company_name:
        return None
    address = ", ".join(part for field in ADDRESS_FIELDS if (part := (row.get(field) or "").strip()))
    return {
        "companies_house_number": company_number,
        "raw_company_name": company_name,
        "company_status": (row.get("CompanyStatus") or "").strip(),
        "sic_codes": ";".join(parse_sic_codes(row)),
        "incorporation_date": parse_incorporation_date(row.get("IncorporationDate")),
        "raw_address": address,
        "postcode": (row.get("RegAddress.PostCode") or "").strip(),
    }


def convert(
    input_paths: list[Path],
    output_csv: Path,
    status_filter: str | None = "Active",
) -> dict[str, object]:
    """Streams one or more snapshot part files into the sampler's population CSV.

    Returns manifest statistics; never loads the whole snapshot into memory.
    """
    rows_read = 0
    rows_kept = 0
    rows_dropped_missing_fields = 0
    status_counts: Counter[str] = Counter()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for input_path in input_paths:
            with input_path.open(newline="", encoding="utf-8-sig") as in_handle:
                # The published snapshot inconsistently pads some header names with a
                # leading space (e.g. " CompanyNumber"); strip before using as dict keys.
                header = [name.strip() for name in next(csv.reader(in_handle))]
                for raw_row in csv.DictReader(in_handle, fieldnames=header):
                    rows_read += 1
                    converted = convert_row(raw_row)
                    if converted is None:
                        rows_dropped_missing_fields += 1
                        continue
                    status_counts[converted["company_status"]] += 1
                    if status_filter is not None and converted["company_status"].upper() != status_filter.upper():
                        continue
                    writer.writerow(converted)
                    rows_kept += 1
    return {
        "input_files": [str(path) for path in input_paths],
        "rows_read": rows_read,
        "rows_dropped_missing_fields": rows_dropped_missing_fields,
        "rows_kept": rows_kept,
        "status_filter": status_filter,
        "status_counts": dict(status_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a manually downloaded Companies House Basic Company Data snapshot "
            "(one or more CSV parts) into the population CSV used by the sampler."
        )
    )
    parser.add_argument("input_csv", type=Path, nargs="+", help="One or more snapshot CSV part files.")
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--status-filter", default="Active", help="Case-insensitive CompanyStatus to keep; pass '' to keep all statuses.")
    parser.add_argument("--snapshot-date", required=True, type=date.fromisoformat, help="As-of date the snapshot claims on the download page, e.g. 2026-08-01.")
    parser.add_argument("--source-url", default="https://download.companieshouse.gov.uk/en_output.html")
    parser.add_argument("--manifest", type=Path, default=Path("data/raw/companies_house_snapshot_manifest.json"))
    args = parser.parse_args()
    status_filter = args.status_filter or None
    stats = convert(args.input_csv, args.output_csv, status_filter=status_filter)
    manifest = {
        "source_url": args.source_url,
        "snapshot_date": args.snapshot_date.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_csv": str(args.output_csv),
        **stats,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
