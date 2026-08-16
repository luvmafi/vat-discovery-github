"""Stable records exchanged between pipeline stages; raw evidence is never discarded."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol


class VerificationStatus(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    VERIFIED = "VERIFIED"
    NOT_REGISTERED = "NOT_REGISTERED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Company:
    companies_house_number: str
    raw_company_name: str
    normalized_company_name: str
    company_status: str
    raw_address: str | None
    normalized_address: str | None
    postcode: str | None
    sic_codes: tuple[str, ...]
    incorporation_date: date | None
    industry_category: str
    age_bucket: str | None


@dataclass(frozen=True)
class VatCandidate:
    company_id: int | None
    raw_vat: str
    normalized_vat: str | None
    source_type: str
    source_url: str
    extraction_method: str
    matched_text: str
    context: str
    discovered_at: datetime
    document_hash: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    vat_number: str
    status: VerificationStatus
    registered_name: str | None
    registered_address: str | None
    effective_date: date | None
    verified_at: datetime
    verifier_source: str
    raw_response_reference: str | None


class VatVerifier(Protocol):
    """Authoritative verifier boundary. Implementations must be rate-limited and auditable."""
    def verify(self, vat_number: str) -> VerificationResult: ...
