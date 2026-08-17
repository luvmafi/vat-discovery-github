"""First website-search pilot for eight companies from the main sample.

Search and page checks were done manually. This is not a run of the future
`SearchProvider` adapter; it is just a small check of whether websites contain
useful VAT evidence.
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ACQUISITION_METHOD = "AGENT_MEDIATED_SEARCH_AND_FETCH"
EXPERIMENT_TIMESTAMP = "2026-08-15T19:45:00+00:00"

# One result per company. Keep the URL even when the search found nothing.
OBSERVATIONS = [
    {
        "companies_house_number": "SL008598",
        "raw_company_name": "CADWELL CORPORATION L.P.",
        "query": '"CADWELL CORPORATION L.P." Edinburgh official website',
        "website_url": None,
        "website_status": None,
        "failure_reason": "NO_WEBSITE_DISCOVERED",
        "vat_evidence_found": False,
        "notes": "Search surfaced an unrelated US medical-device company (Cadwell Industries) and the CH registry page only; no distinct web presence for this LP found.",
    },
    {
        "companies_house_number": "16534631",
        "raw_company_name": "TURQUOISE REAL ESTATE LIMITED",
        "query": '"TURQUOISE REAL ESTATE LIMITED" UK companies house official website',
        "website_url": None,
        "website_status": None,
        "failure_reason": "NO_WEBSITE_DISCOVERED",
        "vat_evidence_found": False,
        "notes": "Confirmed real entity via Companies House (M50 2AB, Active) but search surfaced only differently-numbered same-name-family companies (Turquoise Investment and Capital Ltd, Turquoise Holdings, etc.); none matched this company number or address.",
    },
    {
        "companies_house_number": "15860145",
        "raw_company_name": "KNOTAGAIN INTERNATIONAL LTD",
        "query": '"KNOTAGAIN INTERNATIONAL LTD" official website',
        "website_url": "https://knotagain.co.za/",
        "website_status": "REJECTED",
        "failure_reason": "VERIFIED_WRONG_ENTITY",
        "vat_evidence_found": False,
        "notes": "Only match found was a South African retailer on a .co.za domain; no evidence connecting it to the UK-registered company (CA28 6DG). Rejected as a name collision, not treated as a lead.",
    },
    {
        "companies_house_number": "14145683",
        "raw_company_name": "NORTH LONDON GROUP LTD",
        "query": '"NORTH LONDON GROUP LTD" official website VAT',
        "website_url": "https://www.northlondongroup.co.uk/",
        "website_status": "AMBIGUOUS",
        "failure_reason": "AMBIGUOUS_ENTITY",
        "vat_evidence_found": False,
        "notes": "Companies House confirms real entity at 140 High Road, London, N15 6JN (Active). The candidate domain resolves and loads, but the page carries no company name, address, or registration-number text at all -- only a contact email at an unrelated domain (studio@joshuapress.co.uk), so entity match could not be confirmed. No VAT text present either way.",
    },
    {
        "companies_house_number": "17295865",
        "raw_company_name": "MEAT N SHAKE LTD",
        "query": '"MEAT N SHAKE" restaurant Preston official website',
        "website_url": None,
        "website_status": None,
        "failure_reason": "NO_WEBSITE_DISCOVERED",
        "vat_evidence_found": False,
        "notes": "Query results were dominated by the unrelated US chain 'Steak 'n Shake' (Preston Rd, Frisco TX); no UK result for this company surfaced. Illustrates a generic/brand-adjacent name defeating a single naive search query.",
    },
    {
        "companies_house_number": "17041889",
        "raw_company_name": "GXFC LTD",
        "query": '"GXFC LTD" Croydon official website',
        "website_url": None,
        "website_status": None,
        "failure_reason": "NO_WEBSITE_DISCOVERED",
        "vat_evidence_found": False,
        "notes": "Companies House confirms this GXFC LTD at 378 Lower Addiscombe Road, Croydon, CR0 7AG (Active). Search only surfaced two other, dissolved, differently-numbered companies also named GXFC (Swansea and London E1); neither matches this company.",
    },
    {
        "companies_house_number": "10591912",
        "raw_company_name": "CHURCHGATE WOKING LTD",
        "query": '"CHURCHGATE WOKING LTD" official website',
        "website_url": "http://churchgatehealthcare.co.uk/",
        "website_status": "REJECTED",
        "failure_reason": "WEBSITE_UNREACHABLE",
        "vat_evidence_found": False,
        "notes": "Companies House confirms registered address 227-229 London Road, Romford, RM7 9BQ (Active) -- matching the address a search snippet attributed to this domain, so it looked promising. Fetching it directly failed with DNS resolution error (domain does not currently resolve); could not confirm content or VAT evidence.",
    },
    {
        "companies_house_number": "13523863",
        "raw_company_name": "CEUTICA LIMITED",
        "query": '"CEUTICA LIMITED" Swindon official website',
        "website_url": None,
        "website_status": None,
        "failure_reason": "NO_WEBSITE_DISCOVERED",
        "vat_evidence_found": False,
        "notes": "Companies House confirms this entity at Vicarage Court, 160 Ermin Street, Swindon, SN3 4NE (Active, pharmaceutical manufacturing). Search surfaced only an unrelated same-name Indian pharmaceutical company (ceuticachemie.com); no UK web presence found.",
    },
]


def record(db_path: Path) -> dict[str, object]:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    website_rows_written = 0
    for observation in OBSERVATIONS:
        company_id_row = connection.execute(
            "SELECT company_id FROM companies WHERE companies_house_number = ?",
            (observation["companies_house_number"],),
        ).fetchone()
        if company_id_row is None:
            raise SystemExit(f"Company {observation['companies_house_number']} not found in companies table -- load the sample first.")
        company_id = company_id_row[0]
        if observation["website_url"] is not None:
            connection.execute(
                """INSERT INTO websites (company_id, domain, url, discovery_method, evidence_url, confidence, status, discovered_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(company_id, url) DO NOTHING""",
                (
                    company_id,
                    observation["website_url"].split("/")[2],
                    observation["website_url"],
                    ACQUISITION_METHOD,
                    observation["website_url"],
                    None,
                    observation["website_status"],
                    EXPERIMENT_TIMESTAMP,
                ),
            )
            website_rows_written += 1

    confirmed = sum(1 for o in OBSERVATIONS if o["website_status"] == "CONFIRMED")
    candidate_leads = sum(1 for o in OBSERVATIONS if o["website_url"] is not None)
    vat_evidence = sum(1 for o in OBSERVATIONS if o["vat_evidence_found"])
    n = len(OBSERVATIONS)

    observed_result = {
        "companies_piloted": n,
        "confirmed_entity_matched_websites": confirmed,
        "candidate_leads_found_but_unconfirmed_or_unreachable": candidate_leads,
        "no_website_discovered": sum(1 for o in OBSERVATIONS if o["failure_reason"] == "NO_WEBSITE_DISCOVERED"),
        "verified_wrong_entity": sum(1 for o in OBSERVATIONS if o["failure_reason"] == "VERIFIED_WRONG_ENTITY"),
        "website_unreachable": sum(1 for o in OBSERVATIONS if o["failure_reason"] == "WEBSITE_UNREACHABLE"),
        "vat_evidence_found": vat_evidence,
        "confirmed_website_discovery_rate": confirmed / n,
        "vat_evidence_rate": vat_evidence / n,
    }

    connection.execute(
        """INSERT INTO source_experiments
           (source_name, source_type, hypothesis, population_description, sample_description,
            configuration_version, code_version, started_at, completed_at, observed_result_json,
            failure_modes, conclusion, next_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "Company website (single naive search query per company)",
            "WEB_SEARCH_AND_FETCH",
            "VAT numbers appear frequently enough on official company websites, discoverable via a single "
            "company-name search query, to justify building a scaled search+crawl pipeline.",
            "500-company stratified sample from the 2026-08-01 Companies House active-company snapshot "
            "(see data/processed/sample_manifest.json).",
            "8 companies drawn at even index intervals across the 500-row sample file to span multiple "
            "industry/age strata without cherry-picking easy cases.",
            "phase-1",
            "phase-2-pilot-0.1.0",
            EXPERIMENT_TIMESTAMP,
            EXPERIMENT_TIMESTAMP,
            _json(observed_result),
            "Dominant failure mode: NO_WEBSITE_DISCOVERED (5/8) -- small/recent companies (SPVs, LPs, holding "
            "entities, generic-sounding trading names) have no web presence a single generic search surfaces. "
            "Secondary: name collisions with unrelated same-named companies or international brands defeat a "
            "naive single-query strategy (KNOTAGAIN, MEAT N SHAKE, GXFC, TURQUOISE). One plausible domain had no "
            "identifying content at all (NORTH LONDON GROUP), one plausible domain no longer resolves "
            "(CHURCHGATE WOKING). Zero of 8 produced confirmed entity-matched VAT evidence.",
            "NO-GO for a single-query, first-result search strategy at this sample size.",
            "CONDITIONAL: before concluding on the source itself, run a slightly larger pilot (n=25-30) with "
            "(a) multiple query variants per company (brief section 30's suggested query set, not just one), "
            "and (b) Companies House's own registered SIC/name used to disambiguate multi-result cases, to "
            "separate 'source has no signal' from 'this query strategy is too weak'.",
        ),
    )
    connection.commit()
    connection.close()
    return observed_result


def _json(value: dict) -> str:
    import json
    return json.dumps(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record the Phase-2 website-discovery pilot into the local database.")
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    args = parser.parse_args()
    result = record(args.db)
    print(result)


if __name__ == "__main__":
    main()
