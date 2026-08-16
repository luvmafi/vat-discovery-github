import pytest
from fpdf import FPDF

from vat_discovery.extraction.html import extract_vat_candidates
from vat_discovery.extraction.pdf import content_hash, extract_text, is_pdf


def _make_pdf_bytes(lines: list[str]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 10, text=line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def test_is_pdf_detects_magic_bytes():
    assert is_pdf(b"%PDF-1.7 rest of file") is True
    assert is_pdf(b"<html>not a pdf</html>") is False


def test_content_hash_is_deterministic_and_content_sensitive():
    a = content_hash(b"same bytes")
    b = content_hash(b"same bytes")
    c = content_hash(b"different bytes")
    assert a == b
    assert a != c


def test_extract_text_reads_real_pdf_and_reports_page_stats():
    pdf_bytes = _make_pdf_bytes(["Invoice from Example Fixture Ltd", "VAT Registration Number: GB123456789"])
    result = extract_text(pdf_bytes)
    assert result.extraction_method == "TEXT"
    assert result.page_count == 1
    assert result.pages_with_text == 1
    assert "GB123456789" in result.text
    assert result.content_hash == content_hash(pdf_bytes)


def test_extract_text_output_feeds_the_same_vat_extractor_as_html():
    pdf_bytes = _make_pdf_bytes(["Terms and conditions", "VAT No: GB987654321", "Thank you for your business"])
    result = extract_text(pdf_bytes)
    candidates = extract_vat_candidates(result.text)
    assert any(c.raw_vat == "GB987654321" for c in candidates)


def test_extract_text_rejects_non_pdf_content():
    with pytest.raises(ValueError):
        extract_text(b"<html><body>not a pdf</body></html>")


def test_extract_text_handles_blank_page_without_error():
    pdf_bytes = _make_pdf_bytes([])
    result = extract_text(pdf_bytes)
    assert result.page_count == 1
    assert result.pages_with_text == 0
    assert result.text.strip() == ""
