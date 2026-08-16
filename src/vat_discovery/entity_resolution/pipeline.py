"""Reusable glue: take one piece of first-party-confirmed evidence text and
run it through the real extraction -> normalization -> entity-resolution
pipeline, then persist candidate + document + entity_match rows with full
provenance. Used by every experiment script that finds a real VAT candidate,
so each one doesn't hand-reimplement the same insert logic
(experiments/source_website_round3.py, manual_validation_candidates.py, ...).
"""
from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass

from vat_discovery.entity_resolution.scoring import CandidateEvidence, CompanyRecord, score_match
from vat_discovery.extraction.html import extract_vat_candidates
from vat_discovery.normalization.vat import validate_uk_vat_syntax


@dataclass(frozen=True)
class FirstPartyCandidate:
    companies_house_number: str
    raw_company_name: str
    raw_address: str
    postcode: str
    source_url: str
    source_domain: str
    context_text: str
    timestamp: str


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def process_first_party_candidate(connection: sqlite3.Connection, scoring_config: dict, candidate: FirstPartyCandidate, parser_version: str) -> dict:
    """Extracts, normalizes, scores, and persists one real candidate.
    Raises SystemExit if the company isn't already loaded or the extractor
    finds nothing in the recorded context (a fixture bug, not a real result).
    """
    company_id_row = connection.execute(
        "SELECT company_id FROM companies WHERE companies_house_number = ?",
        (candidate.companies_house_number,),
    ).fetchone()
    if company_id_row is None:
        raise SystemExit(f"Company {candidate.companies_house_number} not found -- load the sample first.")
    company_id = company_id_row[0]

    extracted = extract_vat_candidates(candidate.context_text)
    if not extracted:
        raise SystemExit(f"Extractor found nothing in the recorded context for {candidate.raw_company_name} -- fixture is wrong.")
    top = extracted[0]
    syntax_result = validate_uk_vat_syntax(top.raw_vat)

    connection.execute(
        """INSERT INTO documents (company_id, url, document_type, content_hash, discovered_at, retrieved_at, parser_version, retrieval_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(url) DO NOTHING""",
        (company_id, candidate.source_url, "HTML", _content_hash(candidate.context_text),
         candidate.timestamp, candidate.timestamp, parser_version, "FETCHED_VIA_AGENT_TOOL"),
    )
    document_id_row = connection.execute("SELECT document_id FROM documents WHERE url = ?", (candidate.source_url,)).fetchone()
    document_id = document_id_row[0] if document_id_row else None

    cursor = connection.execute(
        """INSERT INTO vat_candidates
           (company_id, raw_vat, normalized_vat, syntax_valid, syntax_rule, source_type, source_url, document_id,
            extraction_method, matched_text, context, discovered_at, source_document_hash, parser_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (company_id, top.raw_vat, syntax_result.normalized_value, int(syntax_result.syntax_valid), syntax_result.rule,
         "COMPANY_WEBSITE", candidate.source_url, document_id, top.extraction_method, top.matched_text,
         top.context, candidate.timestamp, _content_hash(candidate.context_text), parser_version),
    )
    candidate_id = cursor.lastrowid

    company_record = CompanyRecord(
        companies_house_number=candidate.companies_house_number,
        raw_company_name=candidate.raw_company_name,
        raw_address=candidate.raw_address,
        postcode=candidate.postcode,
        confirmed_domains=frozenset({candidate.source_domain}),
    )
    evidence = CandidateEvidence(
        context_text=candidate.context_text,
        source_domain=candidate.source_domain,
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
        (company_id, candidate.source_domain, candidate.source_url, "AGENT_MEDIATED_SEARCH",
         candidate.source_url, match.total_score, "CONFIRMED", candidate.timestamp),
    )

    return {
        "company": candidate.raw_company_name,
        "raw_vat": top.raw_vat,
        "syntax_valid": syntax_result.syntax_valid,
        "syntax_rule": syntax_result.rule,
        "confidence_tier": match.confidence_tier,
        "decision": match.decision,
        "total_score": round(match.total_score, 3),
    }
