from vat_discovery.normalization.address import normalize_address
from vat_discovery.normalization.company import normalize_company_name
from vat_discovery.normalization.vat import normalize_uk_vat, validate_uk_vat_syntax


def test_vat_presentations_normalize_without_losing_raw_elsewhere():
    assert normalize_uk_vat("GB123456789") == "123456789"
    assert normalize_uk_vat("VAT No: GB 123 4567 89") == "123456789"


def test_checksum_accepts_constructed_standard_number_and_rejects_change():
    first_seven = "1234567"
    check = sum(int(d) * w for d, w in zip(first_seven, (8, 7, 6, 5, 4, 3, 2))) % 97
    valid = f"{first_seven}{check:02d}"
    assert validate_uk_vat_syntax(valid).syntax_valid
    assert not validate_uk_vat_syntax(valid[:-1] + str((int(valid[-1]) + 1) % 10)).syntax_valid


def test_checksum_accepts_constructed_9755_variant_number():
    first_seven = "1234567"
    standard = sum(int(d) * w for d, w in zip(first_seven, (8, 7, 6, 5, 4, 3, 2))) % 97
    legacy_check = (42 - standard) % 97
    valid = f"{first_seven}{legacy_check:02d}"
    result = validate_uk_vat_syntax(valid)
    assert result.syntax_valid
    assert result.rule == "MOD97_55_VARIANT"


def test_checksum_9755_variant_regression_real_first_party_candidates():
    """These three raw digit strings are real VAT numbers found in Phase 10
    manual validation, confirmed on each company's own website footer with an
    exact Companies House company-number match (JTHN LIMITED 08250395, GO2
    PROPERTY SERVICES LIMITED 11369537, G A PLANT AND TOOL HIRE LTD 09460505;
    see docs/findings.md). A sign-flipped 9755 formula rejected all three as
    invalid despite the strong corroborating evidence -- this pinned the fix."""
    assert validate_uk_vat_syntax("183325607").syntax_valid  # JTHN LIMITED
    assert validate_uk_vat_syntax("387741746").syntax_valid  # GO2 PROPERTY SERVICES LIMITED
    assert validate_uk_vat_syntax("208033152").syntax_valid  # G A PLANT AND TOOL HIRE LTD


def test_company_and_address_normalization_are_conservative():
    assert normalize_company_name("J. Smith Building Svcs Ltd.") == "J SMITH BUILDING SVCS LIMITED"
    assert normalize_address("1, High-Street\nLondon") == "1 HIGH STREET LONDON"
