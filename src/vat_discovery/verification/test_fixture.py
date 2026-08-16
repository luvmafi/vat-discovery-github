"""A controlled test-fixture VatVerifier, explicitly sanctioned by the brief
(section 13: "whether verification comes from HMRC API, approved HMRC
mechanism, or controlled test fixture" -- the rest of the pipeline must not
care which). This is NOT a substitute for HMRC verification and must never be
pointed at a real candidate from `data/vat_discovery.sqlite`: every entry
here is a fictional company, invented for this fixture only, so a demo run
can never be mistaken for a real verified result.

Production credentials for the real HMRC "Check a UK VAT Number" API were
identified and the application process was documented (see docs/decision.md)
but not pursued within this project's timeframe -- HMRC's own stated
timeline is approximately two weeks for approval. This fixture exists so the
verification -> entity-resolution -> tiering handoff can be demonstrated
mechanically while that approval is pending, without fabricating a result
for any real company.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from vat_discovery.contracts import VerificationResult, VerificationStatus

_FIXTURE_REGISTRY: dict[str, dict] = {
    "123456715": {  # checksum-valid (MOD97_STANDARD) so the demo isn't confused by an unrelated syntax failure
        "status": VerificationStatus.VERIFIED,
        "registered_name": "EXAMPLE FIXTURE BUILDERS LTD",
        "registered_address": "10 HIGH STREET, ANYTOWN, AB1 2CD",
        "effective_date": date(2015, 3, 1),
    },
    "999999999": {
        "status": VerificationStatus.NOT_REGISTERED,
        "registered_name": None,
        "registered_address": None,
        "effective_date": None,
    },
}


class TestFixtureVerifier:
    """Implements the VatVerifier protocol against the small fictional
    registry above. Any VAT number not in the registry returns UNAVAILABLE,
    matching the honest behaviour used everywhere else in this project when
    no authoritative answer exists -- never inventing a VERIFIED result."""

    def verify(self, vat_number: str) -> VerificationResult:
        entry = _FIXTURE_REGISTRY.get(vat_number)
        now = datetime.now(timezone.utc)
        if entry is None:
            return VerificationResult(
                vat_number=vat_number,
                status=VerificationStatus.UNAVAILABLE,
                registered_name=None,
                registered_address=None,
                effective_date=None,
                verified_at=now,
                verifier_source="TEST_FIXTURE",
                raw_response_reference=None,
            )
        return VerificationResult(
            vat_number=vat_number,
            status=entry["status"],
            registered_name=entry["registered_name"],
            registered_address=entry["registered_address"],
            effective_date=entry["effective_date"],
            verified_at=now,
            verifier_source="TEST_FIXTURE",
            raw_response_reference=f"fixture:{vat_number}",
        )
