"""Records the Phase-4 pilot: public-PDF discovery (search query
`"<company name>" filetype:pdf VAT`) on the same n=8 stratum-spread subset
used in `source_website.py`, for direct comparability.

Same acquisition-method caveat as source_website.py: no credentialed search
API exists yet, so this used the operating agent's own web-search tool
directly (ACQUISITION_METHOD below), not an automated SearchProvider run.

Unlike source_website.py, no candidate PDF was found for any company in this
pilot, so `src/vat_discovery/extraction/pdf.py` was never exercised against a
real downloaded document here -- it remains unit-tested only (see
tests/test_extraction_pdf.py) pending a pilot that actually surfaces a PDF.
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ACQUISITION_METHOD = "AGENT_MEDIATED_SEARCH"
EXPERIMENT_TIMESTAMP = "2026-08-15T20:10:00+00:00"

OBSERVATIONS = [
    {
        "companies_house_number": "SL008598",
        "raw_company_name": "CADWELL CORPORATION L.P.",
        "query": '"CADWELL CORPORATION" Edinburgh filetype:pdf VAT',
        "pdf_found": False,
        "notes": "Only Companies House registry page and unrelated Cadwell-named entities returned; no company-specific PDF.",
    },
    {
        "companies_house_number": "16534631",
        "raw_company_name": "TURQUOISE REAL ESTATE LIMITED",
        "query": '"TURQUOISE REAL ESTATE LIMITED" filetype:pdf VAT',
        "pdf_found": False,
        "notes": "Only differently-numbered same-name-family companies and generic VAT/property guidance PDFs returned.",
    },
    {
        "companies_house_number": "15860145",
        "raw_company_name": "KNOTAGAIN INTERNATIONAL LTD",
        "query": '"KNOTAGAIN INTERNATIONAL" filetype:pdf VAT',
        "pdf_found": False,
        "notes": "No results referencing this company at all; only generic international-VAT guidance documents.",
    },
    {
        "companies_house_number": "14145683",
        "raw_company_name": "NORTH LONDON GROUP LTD",
        "query": '"NORTH LONDON GROUP LTD" filetype:pdf VAT',
        "pdf_found": False,
        "notes": "Companies House overview surfaced; no PDF specific to this company. Results were dominated by unrelated companies literally named 'VAT ...'.",
    },
    {
        "companies_house_number": "17295865",
        "raw_company_name": "MEAT N SHAKE LTD",
        "query": '"MEAT N SHAKE" filetype:pdf VAT registration',
        "pdf_found": False,
        "notes": "Dominated again by the unrelated US chain Steak 'n Shake and generic UK food-VAT guidance; no company-specific document.",
    },
    {
        "companies_house_number": "17041889",
        "raw_company_name": "GXFC LTD",
        "query": '"GXFC LTD" Croydon filetype:pdf VAT',
        "pdf_found": False,
        "notes": "Only differently-numbered same-name companies (France, New Zealand, Australia, two dissolved UK entities) returned; none is this company.",
    },
    {
        "companies_house_number": "10591912",
        "raw_company_name": "CHURCHGATE WOKING LTD",
        "query": '"CHURCHGATE WOKING" filetype:pdf VAT',
        "pdf_found": False,
        "notes": "No results referencing this company; results were dominated by unrelated Woking churches and a Parliamentary VAT-and-churches briefing.",
    },
    {
        "companies_house_number": "13523863",
        "raw_company_name": "CEUTICA LIMITED",
        "query": '"CEUTICA LIMITED" Swindon filetype:pdf VAT',
        "pdf_found": False,
        "notes": "No company-specific result; only generic VAT forms, unrelated VAT-registered-persons lists from other countries, and a Swindon council PDF unrelated to this company.",
    },
]


def record(db_path: Path) -> dict[str, object]:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    for observation in OBSERVATIONS:
        exists = connection.execute(
            "SELECT 1 FROM companies WHERE companies_house_number = ?",
            (observation["companies_house_number"],),
        ).fetchone()
        if exists is None:
            raise SystemExit(f"Company {observation['companies_house_number']} not found -- load the sample first.")

    n = len(OBSERVATIONS)
    pdf_found = sum(1 for o in OBSERVATIONS if o["pdf_found"])
    observed_result = {
        "companies_piloted": n,
        "pdf_candidates_found": pdf_found,
        "pdf_discovery_rate": pdf_found / n,
        "vat_evidence_found": 0,
    }

    connection.execute(
        """INSERT INTO source_experiments
           (source_name, source_type, hypothesis, population_description, sample_description,
            configuration_version, code_version, started_at, completed_at, observed_result_json,
            failure_modes, conclusion, next_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "Public PDFs on/about company (filetype:pdf search query)",
            "SEARCH_FILETYPE_PDF",
            "Public PDFs (invoices, terms, filed documents) discoverable via a filetype:pdf search query "
            "contain VAT evidence for a measurable share of sampled companies.",
            "500-company stratified sample from the 2026-08-01 Companies House active-company snapshot "
            "(see data/processed/sample_manifest.json).",
            "Same 8 companies as the source_website.py pilot, for direct cross-source comparability.",
            "phase-1",
            "phase-4-pilot-0.1.0",
            EXPERIMENT_TIMESTAMP,
            EXPERIMENT_TIMESTAMP,
            _json(observed_result),
            "NO_PUBLIC_VAT_EVIDENCE for all 8: zero company-specific PDFs surfaced at all (not merely PDFs "
            "without VAT text). Results were consistently dominated by (a) unrelated same-named entities in "
            "other countries/registries, (b) generic VAT guidance/compliance documents with no company "
            "connection, and (c) for two companies, results about semantically unrelated topics entirely "
            "(Woking churches for CHURCHGATE WOKING; a US restaurant chain for MEAT N SHAKE).",
            "NO-GO for filetype:pdf search as a standalone discovery signal on this sample. The pdf "
            "extraction module (src/vat_discovery/extraction/pdf.py) is built and unit-tested but has not "
            "been exercised on a real downloaded document, since none was found to fetch.",
            "This pilot could not distinguish 'no PDFs exist for these companies' from 'this query pattern "
            "does not surface them'. A more targeted next step would search a specific known-PDF-heavy source "
            "(e.g. Companies House's own filed accounts PDFs, which do exist for every company but essentially "
            "never contain a VAT number -- accounts and VAT registration are different regimes) rather than "
            "open web search, before writing off public PDFs as a source entirely.",
        ),
    )
    connection.commit()
    connection.close()
    return observed_result


def _json(value: dict) -> str:
    import json
    return json.dumps(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record the Phase-4 public-PDF discovery pilot into the local database.")
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    args = parser.parse_args()
    result = record(args.db)
    print(result)


if __name__ == "__main__":
    main()
