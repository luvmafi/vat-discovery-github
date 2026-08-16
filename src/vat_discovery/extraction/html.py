"""Deterministic VAT-candidate extraction from page/document text.

A match here is only a candidate: raw text plus context. It is never proof of
existence, current registration, or ownership by any particular company —
that requires normalization, syntax/checksum filtering, authoritative
verification, and entity resolution downstream (see normalization.vat and
contracts.VatVerifier).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_VAT_KEYWORD = re.compile(r"VAT(?:\s+(?:No\.?|Number|Reg(?:istration)?(?:\s+Number)?))?", re.I)
_CANDIDATE_NUMBER = re.compile(r"GB\s?\d[\d\s.-]{7,14}\d|\d[\d\s.-]{7,14}\d")
_GB_PREFIXED = re.compile(r"\bGB\s?\d[\d\s.-]{7,14}\d\b")
_TAG_STRIP = re.compile(r"(?s)<[^>]+>")
_SCRIPT_STYLE = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
_ENTITY = re.compile(r"&nbsp;|&amp;|&#\d+;|&\w+;")


@dataclass(frozen=True)
class ExtractedCandidate:
    raw_vat: str
    matched_text: str
    context: str
    extraction_method: str
    span_start: int
    span_end: int


def strip_html_text(html: str) -> str:
    """Best-effort visible-text extraction. Not a full HTML parser; a real
    crawler should prefer a proper parser for anything beyond this POC."""
    text = _SCRIPT_STYLE.sub(" ", html)
    text = _TAG_STRIP.sub(" ", text)
    text = _ENTITY.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_vat_candidates(text: str, context_chars: int = 60) -> list[ExtractedCandidate]:
    """Finds candidates two ways: a number near a VAT-labelling keyword
    (stronger signal), and a bare GB-prefixed 9-digit-shaped number anywhere
    (weaker signal, kept separate so downstream scoring can weight it lower).
    """
    candidates: list[ExtractedCandidate] = []
    covered_spans: list[tuple[int, int]] = []

    for keyword_match in _VAT_KEYWORD.finditer(text):
        window_start = keyword_match.end()
        window_end = min(len(text), window_start + context_chars)
        number_match = _CANDIDATE_NUMBER.search(text[window_start:window_end])
        if not number_match:
            continue
        abs_start = window_start + number_match.start()
        abs_end = window_start + number_match.end()
        if any(start <= abs_start < end for start, end in covered_spans):
            continue
        covered_spans.append((abs_start, abs_end))
        context_from = max(0, keyword_match.start() - context_chars)
        context_to = min(len(text), abs_end + context_chars)
        candidates.append(ExtractedCandidate(
            raw_vat=number_match.group(),
            matched_text=text[keyword_match.start():abs_end],
            context=text[context_from:context_to],
            extraction_method="VAT_KEYWORD_PROXIMITY",
            span_start=abs_start,
            span_end=abs_end,
        ))

    for gb_match in _GB_PREFIXED.finditer(text):
        if any(start <= gb_match.start() < end for start, end in covered_spans):
            continue
        covered_spans.append((gb_match.start(), gb_match.end()))
        context_from = max(0, gb_match.start() - context_chars)
        context_to = min(len(text), gb_match.end() + context_chars)
        candidates.append(ExtractedCandidate(
            raw_vat=gb_match.group(),
            matched_text=gb_match.group(),
            context=text[context_from:context_to],
            extraction_method="GB_PREFIX_PATTERN",
            span_start=gb_match.start(),
            span_end=gb_match.end(),
        ))

    return candidates
