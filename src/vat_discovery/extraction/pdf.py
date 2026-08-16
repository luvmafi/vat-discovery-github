"""PDF text extraction. Deliberately TEXT-layer only: this module never runs
OCR. Per the project brief, OCR is applied only when a specific document is
shown to need it, decided per-document and recorded, not enabled by default
for every PDF (cost/complexity is not justified until measured).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

PDF_MAGIC = b"%PDF-"


@dataclass(frozen=True)
class PdfExtractionResult:
    text: str
    page_count: int
    extraction_method: str
    content_hash: str
    pages_with_text: int


def is_pdf(content: bytes) -> bool:
    return content[:5] == PDF_MAGIC


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_text(content: bytes) -> PdfExtractionResult:
    """Extracts the text layer only. A page contributing zero characters is
    counted but not treated as an error -- some pages are legitimately
    image-only, cover pages, or blank; that is exactly the OCR-need signal
    this module surfaces without acting on it.
    """
    if not is_pdf(content):
        raise ValueError("Content does not start with the PDF magic bytes (%PDF-)")
    try:
        reader = PdfReader(__import__("io").BytesIO(content))
    except PdfReadError as error:
        raise ValueError(f"Unreadable PDF: {error}") from error
    page_texts = []
    pages_with_text = 0
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            pages_with_text += 1
        page_texts.append(text)
    return PdfExtractionResult(
        text="\n".join(page_texts),
        page_count=len(reader.pages),
        extraction_method="TEXT",
        content_hash=content_hash(content),
        pages_with_text=pages_with_text,
    )


def extract_text_from_file(path: Path) -> PdfExtractionResult:
    return extract_text(path.read_bytes())
