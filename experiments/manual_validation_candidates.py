"""Runs candidates from the validation review through the normal pipeline.

Add a record here when a review finds VAT text on the company's own site.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import yaml

from vat_discovery.entity_resolution.pipeline import FirstPartyCandidate, process_first_party_candidate

PARSER_VERSION = "phase-10-0.1.0"

CANDIDATES = [
    FirstPartyCandidate(
        companies_house_number="11369537",
        raw_company_name="GO2 PROPERTY SERVICES LIMITED",
        raw_address="SHALOM HOUSE, 2 DAMASK CLOSE, WEST END, WOKING, SURREY, ENGLAND",
        postcode="GU24 9PD",
        source_url="https://go2.services/contact-us/",
        source_domain="go2.services",
        context_text=(
            "GO2 Property Services Limited, 20 Riverside Avenue, Lightwater, Surrey, England, GU18 5RU. "
            "Company number 11369537. VAT Reg: 3877 41746."
        ),
        timestamp="2026-08-16T12:00:00+00:00",
    ),
    FirstPartyCandidate(
        companies_house_number="09460505",
        raw_company_name="G A PLANT AND TOOL HIRE LTD",
        raw_address="UNIT 1C DARBY CLOSE, CHENEY MANOR INDUSTRIAL ESTATE, SWINDON, ENGLAND",
        postcode="SN2 2PN",
        source_url="https://gaplant.co.uk/contact-us/",
        source_domain="gaplant.co.uk",
        context_text=(
            "G.A. Plant and Tool Hire Ltd, Unit 1c Darby Close, Cheney Manor, Swindon, SN2 2PN. "
            "Registered In England No. 09460505. Vat Registration No. GB 208 0331 52."
        ),
        timestamp="2026-08-16T13:00:00+00:00",
    ),
    FirstPartyCandidate(
        companies_house_number="15093369",
        raw_company_name="TTG PORTSMOUTH LIMITED",
        raw_address="MIDLAND HOUSE, 2 POOLE ROAD, BOURNEMOUTH, ENGLAND",
        postcode="BH2 5QY",
        source_url="https://thetrafalgargroup.co.uk/",
        source_domain="thetrafalgargroup.co.uk",
        context_text=(
            "TTG Portsmouth Ltd: Registered in England and Wales Company Number: 15093369. "
            "Registered Office: Midland House, 2 Poole Road, Bournemouth, Dorset, BH2 5QY. VAT Number: 450 5886 76."
        ),
        timestamp="2026-08-16T14:00:00+00:00",
    ),
    FirstPartyCandidate(
        companies_house_number="11198097",
        raw_company_name="BULLET BUILDING PRODUCTS LIMITED",
        raw_address="BARBOT HALL INDUSTRIAL ESTATE MANGHAM ROAD, GREASBROUGH, ROTHERHAM, ENGLAND",
        postcode="S61 4RJ",
        source_url="https://bulletbuildingproducts.co.uk/contact-us/",
        source_domain="bulletbuildingproducts.co.uk",
        context_text=(
            "Bullet Building Products Ltd, Barbot Hall Industrial Estate, Mangham Road, Rotherham, S61 4RJ. "
            "Company Number: 11198097. VAT Number: 289 184 943."
        ),
        timestamp="2026-08-16T15:00:00+00:00",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Process manual-validation-subset first-party candidates through the real pipeline.")
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    parser.add_argument("--scoring-config", type=Path, default=Path("config/scoring.yaml"))
    args = parser.parse_args()

    connection = sqlite3.connect(args.db)
    connection.execute("PRAGMA foreign_keys = ON")
    scoring_config = yaml.safe_load(args.scoring_config.read_text(encoding="utf-8"))

    results = []
    for candidate in CANDIDATES:
        already_done = connection.execute(
            "SELECT 1 FROM vat_candidates WHERE source_url = ?", (candidate.source_url,)
        ).fetchone()
        if already_done:
            continue
        results.append(process_first_party_candidate(connection, scoring_config, candidate, PARSER_VERSION))
    connection.commit()
    connection.close()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
