"""Phase-2 retest: same 8 companies as source_website.py, but with a
disambiguated query per company (town + sector keyword drawn from the real
Companies House record, e.g. "CEUTICA" Swindon pharmaceutical manufacturing
"VAT number") instead of the original single generic "official website"
query. Tests whether the Phase-2 NO-GO was about the source or the query.

Same ACQUISITION_METHOD caveat as source_website.py: agent-mediated search,
not a live SearchProvider adapter run (no credentials configured).
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ACQUISITION_METHOD = "AGENT_MEDIATED_SEARCH_ROUND_2"
EXPERIMENT_TIMESTAMP = "2026-08-16T10:00:00+00:00"

OBSERVATIONS = [
    {
        "companies_house_number": "SL008598",
        "raw_company_name": "CADWELL CORPORATION L.P.",
        "query": '"CADWELL CORPORATION" Edinburgh "VAT number" real estate',
        "outcome": "NO_WEBSITE_DISCOVERED",
        "notes": "Surfaced several distinct same-name-family companies (Cadwell Real Estate Limited, Cadwell Commercials Limited, Cadwell Group Limited) at different company numbers; none is SL008598. No VAT text for this company.",
    },
    {
        "companies_house_number": "16534631",
        "raw_company_name": "TURQUOISE REAL ESTATE LIMITED",
        "query": '"TURQUOISE REAL ESTATE" Salford "M50 2AB" VAT',
        "outcome": "NO_WEBSITE_DISCOVERED",
        "notes": "Postcode-anchored query returned only generic property-listing/estate-agent sites for the M50 2AB area, none referencing this company by name.",
    },
    {
        "companies_house_number": "15860145",
        "raw_company_name": "KNOTAGAIN INTERNATIONAL LTD",
        "query": '"KNOTAGAIN" Cumbria consultancy "VAT number"',
        "outcome": "NO_WEBSITE_DISCOVERED",
        "notes": "No result referencing this company; returned unrelated VAT-consultancy service providers and an unrelated 'Knott & Co Consultancy Limited'.",
    },
    {
        "companies_house_number": "14145683",
        "raw_company_name": "NORTH LONDON GROUP LTD",
        "query": '"NORTH LONDON GROUP" "N15 6JN" lettings VAT',
        "outcome": "AMBIGUOUS_ENTITY",
        "notes": "Same unresolved candidate domain as round 1 plus an unrelated 'UK North London Lettings Ltd' (different company). Postcode-anchored query did not add a confirming signal.",
    },
    {
        "companies_house_number": "17295865",
        "raw_company_name": "MEAT N SHAKE LTD",
        "query": '"MEAT N SHAKE" Preston restaurant "VAT number"',
        "outcome": "VERIFIED_WRONG_ENTITY",
        "notes": "Surfaced 'MEAT AND SHAKES (PRESTON) LIMITED', company number 13198421, registered at Piccadilly Business Centre, Manchester M12 6AE -- a different company number and address than our sampled MEAT N SHAKE LTD (17295865, PR2 9ZG). A near-name match that would be a dangerous false positive if entity resolution ran on name similarity alone. Rejected after checking the company number, not merged.",
    },
    {
        "companies_house_number": "17041889",
        "raw_company_name": "GXFC LTD",
        "query": '"GXFC" Croydon "CR0 7AG" VAT',
        "outcome": "NO_WEBSITE_DISCOVERED",
        "notes": "Only postcode-area property listings returned. One page incidentally contained an unrelated VAT number ('GB 287 0845 68') on a property listing with no connection to GXFC -- exactly the kind of context-free candidate the extraction/context-scoring design is meant to down-weight, not act on.",
    },
    {
        "companies_house_number": "10591912",
        "raw_company_name": "CHURCHGATE WOKING LTD",
        "query": '"CHURCHGATE WOKING" Romford construction "VAT number"',
        "outcome": "NO_WEBSITE_DISCOVERED",
        "notes": "Confirmed company number 10591912 and address again via search snippet, but VAT number was explicitly reported as not present in any indexed result. Related same-address entities (Churchgate Estates Limited, Churchgate Land Limited) are distinct companies, not this one.",
    },
    {
        "companies_house_number": "13523863",
        "raw_company_name": "CEUTICA LIMITED",
        "query": '"CEUTICA" Swindon pharmaceutical manufacturing "VAT number"',
        "outcome": "NO_WEBSITE_DISCOVERED",
        "notes": "Confirmed company details again but no VAT number surfaced; results were dominated by directory listings of unrelated Swindon pharmaceutical companies.",
    },
]


def record(db_path: Path) -> dict[str, object]:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    n = len(OBSERVATIONS)
    new_confirmed = 0
    new_vat_evidence = 0
    wrong_entity_traps_caught = sum(1 for o in OBSERVATIONS if o["outcome"] == "VERIFIED_WRONG_ENTITY")

    observed_result = {
        "companies_piloted": n,
        "new_confirmed_websites_vs_round_1": new_confirmed,
        "new_vat_evidence_vs_round_1": new_vat_evidence,
        "additional_wrong_entity_traps_identified": wrong_entity_traps_caught,
        "confirmed_website_discovery_rate": new_confirmed / n,
        "vat_evidence_rate": new_vat_evidence / n,
    }

    connection.execute(
        """INSERT INTO source_experiments
           (source_name, source_type, hypothesis, population_description, sample_description,
            configuration_version, code_version, started_at, completed_at, observed_result_json,
            failure_modes, conclusion, next_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "Company website (disambiguated query: town + sector keyword) -- round 2 retest",
            "WEB_SEARCH_AND_FETCH",
            "The round-1 NO-GO was a weak-query artifact, not a source-level ceiling: adding town and sector "
            "disambiguators (drawn from the real Companies House record) to the search query will surface "
            "confirmed websites and/or VAT evidence that the generic single query in round 1 missed.",
            "Same 500-company stratified sample from the 2026-08-01 Companies House snapshot.",
            "Identical 8 companies as source_website.py round 1, for a controlled before/after comparison.",
            "phase-1",
            "phase-2-round2-0.1.0",
            EXPERIMENT_TIMESTAMP,
            EXPERIMENT_TIMESTAMP,
            _json(observed_result),
            "Disambiguation changed the *quality* of near-misses but not the outcome: it surfaced one more "
            "concrete wrong-entity trap (MEAT AND SHAKES (PRESTON) LIMITED, different company number and city "
            "than our MEAT N SHAKE LTD) and one context-free unrelated VAT number on a property listing, both "
            "correctly rejected rather than merged. Zero new confirmed websites, zero new VAT evidence across "
            "all 8 companies on the second, more targeted query.",
            "NOT a query-weakness artifact: disambiguating the query did not change the outcome on this "
            "8-company subset. This raises, not lowers, confidence in the round-1 NO-GO for company websites "
            "as a source for this segment of the population (small/recent companies, generic or "
            "collision-prone names). Combined false-positive evidence (2 concrete wrong-entity near-misses "
            "across both rounds) is a strong argument for never scoring name similarity alone in entity "
            "resolution -- company-number and address evidence must gate any match.",
            "Treat 'company website discovery for small/recently-formed UK companies via open web search' as "
            "a likely-weak source pending a larger, still-unscaled sample; prioritize building entity "
            "resolution scoring now, using these real wrong-entity near-misses as regression fixtures, since "
            "the two false-positive traps found are more instructive than any hypothetical synthetic example "
            "would be.",
        ),
    )
    connection.commit()
    connection.close()
    return observed_result


def _json(value: dict) -> str:
    import json
    return json.dumps(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record the Phase-2 round-2 (disambiguated query) retest.")
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    args = parser.parse_args()
    result = record(args.db)
    print(result)


if __name__ == "__main__":
    main()
