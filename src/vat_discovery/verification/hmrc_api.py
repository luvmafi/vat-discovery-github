"""Real HMRC "Check a UK VAT Number" API v2 adapter, implementing the same
VatVerifier interface as verification.test_fixture.TestFixtureVerifier.

Endpoint details (confirmed against HMRC's published OpenAPI spec, not
guessed): OAuth 2.0 client_credentials grant against
`{base}/oauth/token` with scope `read:vat`, then
`GET {base}/organisations/vat/check-vat-number/lookup/{vrn}` with header
`Accept: application/vnd.hmrc.2.0+json`.

`environment` selects the base URL:
  sandbox    -> https://test-api.service.hmrc.gov.uk (mock data only --
                see HMRC's own test-data VRN list; NEVER real company data)
  production -> https://api.service.hmrc.gov.uk (real data; requires
                approved production credentials, not yet obtained by this
                project -- see docs/decision.md)

`verifier_source` on every result is stamped with the environment
(HMRC_API_SANDBOX / HMRC_API_PRODUCTION) specifically so a sandbox result
can never be mistaken for a real verification downstream.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import requests

from vat_discovery.contracts import VerificationResult, VerificationStatus

_BASE_URLS = {
    "sandbox": "https://test-api.service.hmrc.gov.uk",
    "production": "https://api.service.hmrc.gov.uk",
}


class HmrcVatVerifier:
    def __init__(self, client_id: str, client_secret: str, environment: str = "sandbox", timeout_seconds: int = 20):
        if environment not in _BASE_URLS:
            raise ValueError(f"environment must be one of {list(_BASE_URLS)}, got {environment!r}")
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment = environment
        self.base_url = _BASE_URLS[environment]
        self.timeout_seconds = timeout_seconds
        self._token: str | None = None

    def _get_token(self) -> str:
        if self._token is not None:
            return self._token
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "read:vat",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        return self._token

    def verify(self, vat_number: str) -> VerificationResult:
        now = datetime.now(timezone.utc)
        verifier_source = f"HMRC_API_{self.environment.upper()}"
        try:
            token = self._get_token()
            response = requests.get(
                f"{self.base_url}/organisations/vat/check-vat-number/lookup/{vat_number}",
                headers={
                    "Accept": "application/vnd.hmrc.2.0+json",
                    "Authorization": f"Bearer {token}",
                },
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as error:
            return VerificationResult(
                vat_number=vat_number, status=VerificationStatus.ERROR, registered_name=None,
                registered_address=None, effective_date=None, verified_at=now,
                verifier_source=verifier_source, raw_response_reference=f"network_error:{error}",
            )

        if response.status_code == 404:
            return VerificationResult(
                vat_number=vat_number, status=VerificationStatus.NOT_REGISTERED, registered_name=None,
                registered_address=None, effective_date=None, verified_at=now,
                verifier_source=verifier_source, raw_response_reference=f"http_{response.status_code}",
            )
        if response.status_code != 200:
            return VerificationResult(
                vat_number=vat_number, status=VerificationStatus.ERROR, registered_name=None,
                registered_address=None, effective_date=None, verified_at=now,
                verifier_source=verifier_source, raw_response_reference=f"http_{response.status_code}:{response.text[:200]}",
            )

        body = response.json()
        target = body.get("target", {})
        address = target.get("address") or {}
        address_parts = [address.get("line1"), address.get("line2"), address.get("postcode"), address.get("countryCode")]
        registered_address = ", ".join(part for part in address_parts if part) or None

        return VerificationResult(
            vat_number=vat_number,
            status=VerificationStatus.VERIFIED,
            registered_name=target.get("name"),
            registered_address=registered_address,
            effective_date=_parse_date(target.get("effectiveDate")),
            verified_at=now,
            verifier_source=verifier_source,
            raw_response_reference=body.get("consultationNumber") or "no_consultation_number",
        )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None
