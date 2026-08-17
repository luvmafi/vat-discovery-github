"""Runs the full pipeline with a fake company and test verifier.

It prints the result and does not write demo data into the local database.
"""
from __future__ import annotations

import json

import yaml

from vat_discovery.contracts import VerificationStatus
from vat_discovery.entity_resolution.scoring import CandidateEvidence, CompanyRecord, score_match
from vat_discovery.extraction.html import extract_vat_candidates
from vat_discovery.normalization.vat import validate_uk_vat_syntax
from vat_discovery.verification.test_fixture import TestFixtureVerifier

# Fake company used only by this demo.
FIXTURE_COMPANY = CompanyRecord(
    companies_house_number="01234567",
    raw_company_name="EXAMPLE FIXTURE BUILDERS LTD",
    raw_address="10 High Street, Anytown",
    postcode="AB1 2CD",
)
FIXTURE_CONTEXT_TEXT = (
    "Example Fixture Builders Ltd, 10 High Street, Anytown, AB1 2CD. "
    "Company number 01234567. VAT No: GB123456715."
)


def run() -> dict:
    candidates = extract_vat_candidates(FIXTURE_CONTEXT_TEXT)
    top = candidates[0]

    syntax_result = validate_uk_vat_syntax(top.raw_vat)

    verifier = TestFixtureVerifier()
    verification = verifier.verify(syntax_result.normalized_value)

    evidence = CandidateEvidence(
        context_text=FIXTURE_CONTEXT_TEXT,
        source_domain=None,
        extraction_method=top.extraction_method,
        verification_status=verification.status.value,
    )
    scoring_config = yaml.safe_load(open("config/scoring.yaml", encoding="utf-8"))
    match = score_match(FIXTURE_COMPANY, evidence, scoring_config)

    return {
        "stage_1_extraction": {"raw_vat": top.raw_vat, "extraction_method": top.extraction_method},
        "stage_2_normalization": {"normalized_vat": syntax_result.normalized_value, "syntax_valid": syntax_result.syntax_valid, "rule": syntax_result.rule},
        "stage_3_verification": {
            "status": verification.status.value,
            "registered_name": verification.registered_name,
            "verifier_source": verification.verifier_source,
        },
        "stage_4_entity_resolution": {
            "total_score": round(match.total_score, 3),
            "confidence_tier": match.confidence_tier,
            "decision": match.decision,
        },
        "note": "Fictional demo data only (TestFixtureVerifier). Not written to the real database.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
