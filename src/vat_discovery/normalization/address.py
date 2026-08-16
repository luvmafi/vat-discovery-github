from __future__ import annotations

import re


def normalize_address(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", value.upper())).strip()
