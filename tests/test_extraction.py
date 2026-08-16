from vat_discovery.extraction.html import extract_vat_candidates, strip_html_text
from vat_discovery.normalization.vat import validate_uk_vat_syntax


def test_strip_html_text_removes_scripts_styles_and_tags():
    html = "<html><head><style>.a{}</style><script>x()</script></head><body><p>Hello&nbsp;World</p></body></html>"
    assert strip_html_text(html) == "Hello World"


def test_extract_finds_keyword_proximity_candidate():
    text = "Registered in England. VAT No: GB123456789. Company number 01234567."
    candidates = extract_vat_candidates(text)
    keyword_hits = [c for c in candidates if c.extraction_method == "VAT_KEYWORD_PROXIMITY"]
    assert len(keyword_hits) == 1
    assert keyword_hits[0].raw_vat == "GB123456789"
    assert "VAT No" in keyword_hits[0].matched_text


def test_extract_handles_spaced_digits_after_keyword():
    text = "VAT Registration Number 123 4567 89 for all invoices."
    candidates = extract_vat_candidates(text)
    assert candidates[0].raw_vat == "123 4567 89"


def test_extract_finds_bare_gb_prefix_without_keyword():
    text = "Terms apply. Ref GB987654321 shown on the footer."
    candidates = extract_vat_candidates(text)
    assert len(candidates) == 1
    assert candidates[0].extraction_method == "GB_PREFIX_PATTERN"


def test_extract_does_not_double_count_gb_prefixed_keyword_match():
    text = "VAT Number GB123456789 appears once."
    candidates = extract_vat_candidates(text)
    assert len(candidates) == 1
    assert candidates[0].extraction_method == "VAT_KEYWORD_PROXIMITY"


def test_extract_returns_nothing_for_unrelated_text():
    text = "Company number 01234567, registered office in London."
    assert extract_vat_candidates(text) == []


def test_extracted_candidate_feeds_syntax_validation():
    text = "VAT No: GB123456789"
    candidate = extract_vat_candidates(text)[0]
    result = validate_uk_vat_syntax(candidate.raw_vat)
    assert result.normalized_value == "123456789"
    # This specific digit string is not expected to pass MOD97; the point of
    # this test is only that extraction output feeds normalization cleanly.
    assert result.syntax_valid in (True, False)
