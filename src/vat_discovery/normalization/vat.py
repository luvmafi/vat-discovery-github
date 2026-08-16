"""Normalization and *format* validation only; never authoritative verification."""
from __future__ import annotations

import re
from dataclasses import dataclass

_PREFIX = re.compile(r"^(?:VAT(?:\s+(?:NO|NUMBER|REG(?:ISTRATION)?))?\s*[:#-]?\s*)?GB\s*", re.I)


@dataclass(frozen=True)
class VatSyntaxResult:
    normalized_value: str | None
    syntax_valid: bool
    rule: str | None
    reason: str | None


def normalize_uk_vat(raw_value: str) -> str | None:
    """Return nine numeric digits after removing a GB/VAT presentation prefix, else None."""
    text = _PREFIX.sub("", raw_value.strip())
    digits = re.sub(r"[\s.-]", "", text)
    return digits if digits.isascii() and digits.isdigit() and len(digits) == 9 else None


def validate_uk_vat_syntax(raw_value: str) -> VatSyntaxResult:
    value = normalize_uk_vat(raw_value)
    if value is None:
        return VatSyntaxResult(None, False, None, "Expected nine numeric digits after an optional GB/VAT prefix")
    weighted_sum = sum(int(digit) * weight for digit, weight in zip(value[:7], (8, 7, 6, 5, 4, 3, 2)))
    check_digits = int(value[7:])
    standard = weighted_sum % 97
    # Registrations from Nov 2009 onward may use the documented "9755" variant:
    # check = (42 - standard) mod 97, not (standard + 42) mod 97 -- confirmed
    # against three real first-party-sourced VAT numbers found during Phase 10
    # manual validation (JTHN LIMITED, GO2 PROPERTY SERVICES LIMITED,
    # G A PLANT AND TOOL HIRE LTD) that a sign-flipped version of this formula
    # incorrectly rejected. This is only a filter, never proof either way.
    legacy = (42 - standard) % 97
    if check_digits == standard:
        return VatSyntaxResult(value, True, "MOD97_STANDARD", None)
    if check_digits == legacy:
        return VatSyntaxResult(value, True, "MOD97_55_VARIANT", None)
    return VatSyntaxResult(value, False, None, "Checksum does not match a supported MOD97 rule")
