from __future__ import annotations

import re

_SUFFIXES = re.compile(r"\b(LIMITED|LTD)\.?\b", re.I)


def normalize_company_name(value: str) -> str:
    """Conservative comparison form; preserve the raw name separately."""
    value = value.upper().replace("&", " AND ")
    value = _SUFFIXES.sub(" LIMITED ", value)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", value)).strip()
