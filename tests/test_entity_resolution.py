from pathlib import Path

import yaml

from vat_discovery.entity_resolution.scoring import CandidateEvidence, CompanyRecord, score_match

CONFIG = yaml.safe_load(Path("config/scoring.yaml").read_text(encoding="utf-8"))


def test_clean_positive_case_reaches_tier_1():
    company = CompanyRecord(
        companies_house_number="01234567",
        raw_company_name="ABC BUILDERS LTD",
        raw_address="10 High Street, Anytown",
        postcode="AB1 2CD",
    )
    evidence = CandidateEvidence(
        context_text="ABC Builders Ltd, 10 High Street, Anytown, AB1 2CD. Company number 01234567. VAT No: GB123456789.",
        source_domain=None,
        extraction_method="VAT_KEYWORD_PROXIMITY",
        verification_status="VERIFIED",
    )
    result = score_match(company, evidence, CONFIG)
    assert result.confidence_tier == "TIER_1"
    assert result.decision == "ACCEPT_HIGH_CONFIDENCE"
    assert result.postcode_match is True
    assert result.company_number_match is True


def test_unverified_candidate_never_exceeds_tier_3_even_with_perfect_context():
    company = CompanyRecord(
        companies_house_number="01234567",
        raw_company_name="ABC BUILDERS LTD",
        raw_address="10 High Street, Anytown",
        postcode="AB1 2CD",
    )
    evidence = CandidateEvidence(
        context_text="ABC Builders Ltd, 10 High Street, Anytown, AB1 2CD. Company number 01234567. VAT No: GB123456789.",
        source_domain=None,
        extraction_method="VAT_KEYWORD_PROXIMITY",
        verification_status="UNAVAILABLE",
    )
    result = score_match(company, evidence, CONFIG)
    assert result.confidence_tier == "TIER_3"
    assert result.decision == "CANDIDATE_ONLY_NOT_A_DISCOVERY"


def test_real_wrong_entity_case_knotagain_does_not_reach_high_confidence():
    """Regression fixture from the Phase-2 pilot: KNOTAGAIN INTERNATIONAL LTD
    (UK, Cumbria, company number 15860145) vs. the only web evidence found,
    a same-named South African retailer's site with no UK company details."""
    company = CompanyRecord(
        companies_house_number="15860145",
        raw_company_name="KNOTAGAIN INTERNATIONAL LTD",
        raw_address="Cleator Moor, Cumbria",
        postcode="CA28 6DG",
    )
    evidence = CandidateEvidence(
        context_text="Classic Style, Made Just for You. KnotAgain - Atensi Series, Ayana Jute Tote. South Africa.",
        source_domain="knotagain.co.za",
        extraction_method="GB_PREFIX_PATTERN",
        verification_status="VERIFIED",
    )
    result = score_match(company, evidence, CONFIG)
    assert result.confidence_tier == "TIER_3"
    assert result.postcode_match is False
    assert result.company_number_match is False


def test_real_wrong_entity_case_meat_n_shake_rejected_despite_partial_name_overlap():
    """Regression fixture: MEAT N SHAKE LTD (17295865, Preston PR2 9ZG) vs.
    context describing the differently-numbered MEAT AND SHAKES (PRESTON)
    LIMITED (13198421, Manchester M12 6AE). Name tokens partially overlap
    ("MEAT", "SHAKE(S)") but address/company-number evidence contradicts."""
    company = CompanyRecord(
        companies_house_number="17295865",
        raw_company_name="MEAT N SHAKE LTD",
        raw_address="Preston",
        postcode="PR2 9ZG",
    )
    evidence = CandidateEvidence(
        context_text="MEAT AND SHAKES (PRESTON) LIMITED, company number 13198421, Piccadilly Business Centre, "
                      "Aldow Enterprise Park, Manchester, M12 6AE. VAT No: GB999999999.",
        source_domain=None,
        extraction_method="VAT_KEYWORD_PROXIMITY",
        verification_status="VERIFIED",
    )
    result = score_match(company, evidence, CONFIG)
    assert result.confidence_tier != "TIER_1"
    assert result.postcode_match is False
    assert result.company_number_match is False


def test_context_free_gb_prefix_candidate_scores_low_context():
    company = CompanyRecord(
        companies_house_number="17041889",
        raw_company_name="GXFC LTD",
        raw_address="378 Lower Addiscombe Road, Croydon",
        postcode="CR0 7AG",
    )
    evidence = CandidateEvidence(
        context_text="House prices for 404 Lower Addiscombe Road. Ref GB287084568 shown on listing.",
        source_domain=None,
        extraction_method="GB_PREFIX_PATTERN",
        verification_status="VERIFIED",
    )
    result = score_match(company, evidence, CONFIG)
    assert result.context_score < 1.0
    assert result.confidence_tier != "TIER_1"


def test_medium_confidence_case_with_partial_corroboration():
    """Name matches, evidence comes from the company's own confirmed domain,
    and most (not all) of the address is present -- but neither postcode nor
    company number appear, so this must land below TIER_1's required
    corroboration even though the total score clears the medium threshold."""
    company = CompanyRecord(
        companies_house_number="09876543",
        raw_company_name="RIVERSIDE CONSULTING LIMITED",
        raw_address="5 Quay Street, Rivertown",
        postcode="RT1 1QT",
        confirmed_domains=frozenset({"riverside-consulting.co.uk"}),
    )
    evidence = CandidateEvidence(
        context_text="Riverside Consulting Limited, Quay Street, Rivertown. VAT Number GB135792468.",
        source_domain="riverside-consulting.co.uk",
        extraction_method="VAT_KEYWORD_PROXIMITY",
        verification_status="VERIFIED",
    )
    result = score_match(company, evidence, CONFIG)
    assert result.postcode_match is False
    assert result.company_number_match is False
    assert result.domain_score == 1.0
    assert result.confidence_tier == "TIER_2"
    assert result.decision == "ACCEPT_MEDIUM_CONFIDENCE_MANUAL_REVIEW"


def test_explanation_is_always_populated():
    company = CompanyRecord(companies_house_number="1", raw_company_name="X LTD", raw_address=None, postcode=None)
    evidence = CandidateEvidence(context_text="irrelevant", source_domain=None, extraction_method="OTHER", verification_status="NOT_REGISTERED")
    result = score_match(company, evidence, CONFIG)
    assert len(result.explanation) >= 6
