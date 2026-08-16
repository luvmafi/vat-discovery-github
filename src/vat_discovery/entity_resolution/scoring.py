"""Multi-signal entity resolution: does this VAT candidate's evidence context
actually belong to this Companies House company? Every signal is explainable
and independently inspectable; nothing here is a black-box similarity score.

Design intent (see docs/methodology.md and the project brief section 15-17):
name similarity alone is never sufficient -- two real near-misses found during
Phase-2 piloting (KNOTAGAIN INTERNATIONAL LTD vs. an unrelated South African
retailer of the same name; MEAT N SHAKE LTD vs. the differently-numbered
MEAT AND SHAKES (PRESTON) LIMITED) are used as regression fixtures in
tests/test_entity_resolution.py precisely because they are real, not
hypothetical.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from vat_discovery.normalization.address import normalize_address
from vat_discovery.normalization.company import normalize_company_name

_GENERIC_NAME_TOKENS = frozenset({"LIMITED", "LTD", "AND", "THE", "OF", "LP", "LLP"})


@dataclass(frozen=True)
class CompanyRecord:
    companies_house_number: str
    raw_company_name: str
    raw_address: str | None
    postcode: str | None
    confirmed_domains: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class CandidateEvidence:
    context_text: str
    source_domain: str | None
    extraction_method: str
    verification_status: str


@dataclass(frozen=True)
class MatchResult:
    name_score: float
    address_score: float
    postcode_match: bool
    domain_score: float
    company_number_match: bool
    context_score: float
    total_score: float
    confidence_tier: str
    decision: str
    explanation: tuple[str, ...]


def _name_tokens(raw_name: str) -> set[str]:
    return {token for token in normalize_company_name(raw_name).split() if token not in _GENERIC_NAME_TOKENS}


def _address_tokens(raw_address: str | None) -> set[str]:
    normalized = normalize_address(raw_address)
    return set(normalized.split()) if normalized else set()


def _clean_for_matching(text: str) -> str:
    """Uppercase, strip punctuation to whitespace. Used for all haystack
    comparisons so a trailing comma/period never breaks a token match."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]", " ", text.upper())).strip()


def _token_containment(needle_tokens: set[str], haystack_text: str) -> float:
    """Fraction of needle_tokens present as whole words in haystack_text.
    Containment, not Jaccard: haystack is free-form context, expected to
    contain far more than just the entity's own tokens."""
    if not needle_tokens:
        return 0.0
    haystack_tokens = set(_clean_for_matching(haystack_text).split())
    return len(needle_tokens & haystack_tokens) / len(needle_tokens)


def _extraction_method_context_score(extraction_method: str) -> float:
    return {"VAT_KEYWORD_PROXIMITY": 1.0, "GB_PREFIX_PATTERN": 0.5}.get(extraction_method, 0.3)


def score_match(company: CompanyRecord, evidence: CandidateEvidence, config: dict) -> MatchResult:
    context_clean = _clean_for_matching(evidence.context_text)
    normalized_context = normalize_company_name(evidence.context_text)

    name_score = _token_containment(_name_tokens(company.raw_company_name), normalized_context)
    address_score = _token_containment(_address_tokens(company.raw_address), context_clean)
    postcode_match = bool(company.postcode) and _clean_for_matching(company.postcode) in context_clean
    company_number_match = _clean_for_matching(company.companies_house_number) in context_clean
    domain_score = 1.0 if evidence.source_domain and evidence.source_domain in company.confirmed_domains else 0.0
    context_score = _extraction_method_context_score(evidence.extraction_method)

    weights = config["weights"]
    signal_values = {
        "name_score": name_score,
        "address_score": address_score,
        "postcode_match": float(postcode_match),
        "domain_score": domain_score,
        "company_number_match": float(company_number_match),
        "context_score": context_score,
    }
    total_score = sum(weights[key] * signal_values[key] for key in weights)

    tiers = config["tiers"]
    required = config["required_for_high_confidence"]
    is_verified = evidence.verification_status == required["verification_status"]
    has_required_corroboration = any(signal_values.get(name, 0.0) >= 1.0 for name in required["one_of"])

    if is_verified and total_score >= tiers["high_confidence_min"] and has_required_corroboration:
        confidence_tier, decision = "TIER_1", "ACCEPT_HIGH_CONFIDENCE"
    elif is_verified and total_score >= tiers["medium_confidence_min"]:
        confidence_tier, decision = "TIER_2", "ACCEPT_MEDIUM_CONFIDENCE_MANUAL_REVIEW"
    else:
        confidence_tier, decision = "TIER_3", "CANDIDATE_ONLY_NOT_A_DISCOVERY"

    explanation = [
        f"name_score={name_score:.2f} (containment of non-generic company-name tokens in context)",
        f"address_score={address_score:.2f} (containment of address tokens in context)",
        f"postcode_match={postcode_match}",
        f"company_number_match={company_number_match}",
        f"domain_score={domain_score:.2f} (evidence domain vs. confirmed domains for this company)",
        f"context_score={context_score:.2f} (extraction_method={evidence.extraction_method})",
        f"total_score={total_score:.3f}, verification_status={evidence.verification_status}",
    ]
    if not is_verified:
        explanation.append("Not VERIFIED by an authoritative verifier -- cannot exceed TIER_3 regardless of score.")
    elif confidence_tier == "TIER_2":
        explanation.append(f"Below TIER_1 corroboration requirement (needs one of {required['one_of']} at 1.0).")

    return MatchResult(
        name_score=name_score,
        address_score=address_score,
        postcode_match=postcode_match,
        domain_score=domain_score,
        company_number_match=company_number_match,
        context_score=context_score,
        total_score=total_score,
        confidence_tier=confidence_tier,
        decision=decision,
        explanation=tuple(explanation),
    )
