"""Third website-search round with 28 new companies.

Two candidates were found on company sites and go through the same extraction
and matching code as everything else. They stay at TIER_3 because there is no
HMRC production check. An AQUAWASH claim from a search summary was not on the
actual page, so it was not saved as evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path

import yaml

from vat_discovery.entity_resolution.scoring import CandidateEvidence, CompanyRecord, score_match
from vat_discovery.extraction.html import extract_vat_candidates
from vat_discovery.normalization.vat import validate_uk_vat_syntax

ACQUISITION_METHOD = "AGENT_MEDIATED_SEARCH_ROUND_3"
EXPERIMENT_TIMESTAMP = "2026-08-16T11:00:00+00:00"

# Negative results for this round. The earlier rounds have fuller notes.
NEGATIVE_OBSERVATIONS = [
    ("06852397", "LOCUS SOLUS LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("15165211", "CODATA LTD", "NO_WEBSITE_DISCOVERED"),
    ("11503460", "SPIRITLAND PRODUCTIONS LIMITED", "NO_VAT_ON_CONFIRMED_SITE"),  # site found, no VAT text surfaced in search
    ("16696805", "WRIGHT WASTE DISPOSAL LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("17141961", "SANDY B ESTATES LTD", "NO_WEBSITE_DISCOVERED"),
    ("16304368", "TED ACCOUNTANTS LTD", "NO_WEBSITE_DISCOVERED"),
    ("16429901", "HRICHAT LTD", "NO_WEBSITE_DISCOVERED"),
    ("09793840", "PATMU LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("12385452", "WESTRIVE MENTORING LTD", "NO_VAT_ON_CONFIRMED_SITE"),
    ("14907803", "TOGAN FACILITY MANAGEMENT LTD", "NO_WEBSITE_DISCOVERED"),
    ("14220123", "ZEDWELL LSQ LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("04766775", "CREDENTIAL LIMITED", "NO_VAT_ON_CONFIRMED_SITE"),
    ("SL004250", "PATRICOF (NO. 2) YELL DDB L.P.", "NO_WEBSITE_DISCOVERED"),
    ("07181158", "FESTIVE LIZARDS LTD", "NO_WEBSITE_DISCOVERED"),
    ("01865021", "FAZAL FAST FOODS LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("15550338", "WYLDTHINGSUK LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("16604812", "HALLELUJAH HALLELUJAH LTD", "NO_WEBSITE_DISCOVERED"),
    ("08210607", "WALKERS ELECTRICAL SERVICES (HARVINGTON) LIMITED", "NO_VAT_ON_CONFIRMED_SITE"),
    ("04553758", "REBEL FUTURES LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("16893516", "H AND D TRANSPORT LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("04662659", "SHERIDAN COOPER'S LIMITED", "NO_WEBSITE_DISCOVERED"),
    ("SC147010", "AQUAWASH LIMITED", "UNCONFIRMED_SEARCH_SUMMARY_CLAIM_REJECTED"),
    ("12670280", "K.O.H. SPORTCARDS LTD", "NO_WEBSITE_DISCOVERED"),
    ("NI670011", "TGK FOODS LTD", "UNCONFIRMED_THIRD_PARTY_CLAIM_ONLY"),
    ("13464918", "BROTHERS JET COMPANY LTD", "NO_WEBSITE_DISCOVERED"),
    ("16825167", "BRISTOLMEATS LIMITED", "NO_WEBSITE_DISCOVERED"),
]

# Candidates found on their own sites. Run them through the usual pipeline.
POSITIVE_CANDIDATES = [
    {
        "companies_house_number": "14228579",
        "raw_company_name": "HILLS FAMILY LTD",
        "raw_address": "128 CITY ROAD, LONDON, UNITED KINGDOM",
        "postcode": "EC1V 2NX",
        "source_url": "https://hills-family.ltd.uk/",
        "source_domain": "hills-family.ltd.uk",
        "context_text": (
            "Hills Family Ltd, 128 City Road, London. EC1V 2NX, United Kingdom. "
            "VAT No. 420840821. Company Registration No. 14228579, Registered in England and Wales."
        ),
        "address_discrepancy": None,
    },
    {
        "companies_house_number": "08250395",
        "raw_company_name": "JTHN LIMITED",
        "raw_address": "LIME HOUSE 75 CHURCH ROAD, TIPTREE, COLCHESTER, ENGLAND",
        "postcode": "CO5 0HB",
        "source_url": "https://www.jthn.co.uk/our-policies/",
        "source_domain": "www.jthn.co.uk",
        "context_text": (
            "JTHN Ltd, 65 Church Road, Tiptree, Essex CO5 0ST. "
            "VAT Registration Number 183 3256 07. Registered in England No. 08250395."
        ),
        "address_discrepancy": (
            "Website footer address (65 Church Road, Tiptree, Essex CO5 0ST) does not exactly match the "
            "Companies House registered address (Lime House, 75 Church Road, Tiptree, Colchester, CO5 0HB), "
            "confirmed directly against the live Companies House record before accepting this candidate. "
            "Company number match (08250395, exact) is treated as sufficient corroboration per "
            "config/scoring.yaml regardless of the address string mismatch -- plausibly a trading-address vs. "
            "registered-office difference, not investigated further here."
        ),
    },
]


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def process_positive_candidates(connection: sqlite3.Connection, scoring_config: dict) -> list[dict]:
    results = []
    for candidate in POSITIVE_CANDIDATES:
        company_id_row = connection.execute(
            "SELECT company_id FROM companies WHERE companies_house_number = ?",
            (candidate["companies_house_number"],),
        ).fetchone()
        if company_id_row is None:
            raise SystemExit(f"Company {candidate['companies_house_number']} not found -- load the sample first.")
        company_id = company_id_row[0]

        extracted = extract_vat_candidates(candidate["context_text"])
        if not extracted:
            raise SystemExit(f"Extractor found nothing in the recorded context for {candidate['raw_company_name']} -- fixture is wrong.")
        top = extracted[0]
        syntax_result = validate_uk_vat_syntax(top.raw_vat)

        connection.execute(
            """INSERT INTO documents (company_id, url, document_type, content_hash, discovered_at, retrieved_at, parser_version, retrieval_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(url) DO NOTHING""",
            (company_id, candidate["source_url"], "HTML", _content_hash(candidate["context_text"]),
             EXPERIMENT_TIMESTAMP, EXPERIMENT_TIMESTAMP, "phase-2-round3-0.1.0", "FETCHED_VIA_AGENT_TOOL"),
        )
        document_id_row = connection.execute("SELECT document_id FROM documents WHERE url = ?", (candidate["source_url"],)).fetchone()
        document_id = document_id_row[0] if document_id_row else None

        cursor = connection.execute(
            """INSERT INTO vat_candidates
               (company_id, raw_vat, normalized_vat, syntax_valid, syntax_rule, source_type, source_url, document_id,
                extraction_method, matched_text, context, discovered_at, source_document_hash, parser_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (company_id, top.raw_vat, syntax_result.normalized_value, int(syntax_result.syntax_valid), syntax_result.rule,
             "COMPANY_WEBSITE", candidate["source_url"], document_id, top.extraction_method, top.matched_text,
             top.context, EXPERIMENT_TIMESTAMP, _content_hash(candidate["context_text"]), "phase-3-0.1.0"),
        )
        candidate_id = cursor.lastrowid

        company_record = CompanyRecord(
            companies_house_number=candidate["companies_house_number"],
            raw_company_name=candidate["raw_company_name"],
            raw_address=candidate["raw_address"],
            postcode=candidate["postcode"],
            confirmed_domains=frozenset({candidate["source_domain"]}),
        )
        evidence = CandidateEvidence(
            context_text=candidate["context_text"],
            source_domain=candidate["source_domain"],
            extraction_method=top.extraction_method,
            verification_status="UNAVAILABLE",  # honest: no HMRC credentials, no authoritative verification performed
        )
        match = score_match(company_record, evidence, scoring_config)

        connection.execute(
            """INSERT INTO entity_matches
               (candidate_id, company_id, name_score, address_score, postcode_match, domain_score, company_number_match,
                context_score, total_score, confidence_tier, decision, explanation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, company_id, match.name_score, match.address_score, int(match.postcode_match), match.domain_score,
             int(match.company_number_match), match.context_score, match.total_score, match.confidence_tier, match.decision,
             "; ".join(match.explanation)),
        )

        connection.execute(
            """INSERT INTO websites (company_id, domain, url, discovery_method, evidence_url, confidence, status, discovered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(company_id, url) DO NOTHING""",
            (company_id, candidate["source_domain"], candidate["source_url"], ACQUISITION_METHOD,
             candidate["source_url"], match.total_score, "CONFIRMED", EXPERIMENT_TIMESTAMP),
        )

        results.append({
            "company": candidate["raw_company_name"],
            "raw_vat": top.raw_vat,
            "syntax_valid": syntax_result.syntax_valid,
            "syntax_rule": syntax_result.rule,
            "confidence_tier": match.confidence_tier,
            "decision": match.decision,
            "total_score": round(match.total_score, 3),
            "address_discrepancy": candidate["address_discrepancy"],
        })
    return results


def record(db_path: Path, scoring_config_path: Path) -> dict[str, object]:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    scoring_config = yaml.safe_load(scoring_config_path.read_text(encoding="utf-8"))

    for company_number, _, _ in NEGATIVE_OBSERVATIONS:
        exists = connection.execute("SELECT 1 FROM companies WHERE companies_house_number = ?", (company_number,)).fetchone()
        if exists is None:
            raise SystemExit(f"Company {company_number} not found -- load the sample first.")

    positive_results = process_positive_candidates(connection, scoring_config)

    n_new = len(NEGATIVE_OBSERVATIONS) + len(POSITIVE_CANDIDATES)
    observed_result = {
        "new_companies_piloted_round_3": n_new,
        "cumulative_companies_piloted_all_rounds": 8 + n_new,  # round 1/2 shared the same 8; round 3 adds n_new distinct new ones
        "confirmed_first_party_vat_candidates": len(positive_results),
        "candidates": positive_results,
        "confirmed_website_discovery_rate_round_3": len(positive_results) / n_new,
        "no_website_discovered": sum(1 for _, _, o in NEGATIVE_OBSERVATIONS if o == "NO_WEBSITE_DISCOVERED"),
        "website_found_but_no_vat": sum(1 for _, _, o in NEGATIVE_OBSERVATIONS if o == "NO_VAT_ON_CONFIRMED_SITE"),
        "rejected_unconfirmed_claims": sum(1 for _, _, o in NEGATIVE_OBSERVATIONS if "UNCONFIRMED" in o),
    }

    connection.execute(
        """INSERT INTO source_experiments
           (source_name, source_type, hypothesis, population_description, sample_description,
            configuration_version, code_version, started_at, completed_at, observed_result_json,
            failure_modes, conclusion, next_action)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "Company website (disambiguated query) -- round 3, extended pilot (n=28 new + 2 reused)",
            "WEB_SEARCH_AND_FETCH",
            "Scaling the disambiguated-query strategy from n=8 to n~30 will surface a measurable, non-zero rate "
            "of first-party VAT evidence, large enough to inform a GO/CONDITIONAL GO/NO-GO read on this source.",
            "500-company stratified sample from the 2026-08-01 Companies House active-company snapshot.",
            "28 new companies at even index spacing across the 500-row sample (i*500/30), plus the 2 "
            "already-tested overlapping companies from rounds 1-2 (not re-queried); cumulative 36 distinct "
            "companies piloted across all three rounds.",
            "phase-1",
            "phase-2-round3-0.1.0",
            EXPERIMENT_TIMESTAMP,
            EXPERIMENT_TIMESTAMP,
            _json(observed_result),
            "2 of 28 new companies (7%) produced a real, first-party-confirmed VAT candidate on their own "
            "website footer (HILLS FAMILY LTD, JTHN LIMITED) -- the first positive results across 36 companies "
            "and three rounds. Both required direct WebFetch verification of the actual page; search-summary "
            "text alone was not trusted. One claimed VAT number (AQUAWASH LIMITED) reported in a search "
            "summary was NOT present on the cited page when fetched directly -- rejected as an unconfirmed, "
            "possibly hallucinated claim, not merged as evidence. One other claim (TGK FOODS LTD) was "
            "consistent across only third-party aggregator sites with no first-party page found to confirm "
            "it -- also not merged. JTHN's own website address differs from its Companies House registered "
            "address; accepted anyway on exact company-number match, per the project's own required-signal "
            "design, with the discrepancy explicitly logged.",
            "Neither confirmed candidate reaches TIER_1: both are capped at TIER_3 by verification_status="
            "UNAVAILABLE, since no HMRC credentials exist to authoritatively verify them -- this is the "
            "designed behaviour, not a bug. Revised read: company websites ARE a real, non-zero signal at "
            "roughly 5-10% of companies (2/28 this round; 0/8 in the smaller rounds 1-2, consistent with a low "
            "single-digit-to-low-teens rate needing a larger n to pin down). CONDITIONAL GO for company-website "
            "discovery as a source, pending an authoritative verifier.",
            "Converting a TIER_3 candidate to a reportable discovery requires either real HMRC verifier "
            "credentials or an explicitly documented alternative authoritative check -- that gap, not "
            "discovery itself, is now the binding constraint on this pipeline. Next: pursue HMRC API "
            "onboarding/credentials (see hmrc_experiment.py's dry-run scaffold), and separately, scale this "
            "query strategy further (n=100+) now that it has a measured non-zero base rate to estimate from.",
        ),
    )
    connection.commit()
    connection.close()
    return observed_result


def _json(value: dict) -> str:
    import json
    return json.dumps(value, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record the Phase-2 round-3 extended pilot (n~30) into the local database.")
    parser.add_argument("--db", type=Path, default=Path("data/vat_discovery.sqlite"))
    parser.add_argument("--scoring-config", type=Path, default=Path("config/scoring.yaml"))
    args = parser.parse_args()
    result = record(args.db, args.scoring_config)
    print(_json(result))


if __name__ == "__main__":
    main()
