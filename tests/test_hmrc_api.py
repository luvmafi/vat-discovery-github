from datetime import date

import pytest

from vat_discovery.contracts import VerificationStatus
from vat_discovery.verification.hmrc_api import HmrcVatVerifier


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_body = json_body or {}
        self.text = text

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_rejects_unknown_environment():
    with pytest.raises(ValueError):
        HmrcVatVerifier("id", "secret", environment="staging")


def test_sandbox_uses_test_api_base_url():
    verifier = HmrcVatVerifier("id", "secret", environment="sandbox")
    assert verifier.base_url == "https://test-api.service.hmrc.gov.uk"


def test_production_uses_real_api_base_url():
    verifier = HmrcVatVerifier("id", "secret", environment="production")
    assert verifier.base_url == "https://api.service.hmrc.gov.uk"


def test_verify_success_parses_result_and_stamps_environment(monkeypatch):
    verifier = HmrcVatVerifier("id", "secret", environment="sandbox")

    def fake_post(url, data, timeout):
        assert url.endswith("/oauth/token")
        assert data["grant_type"] == "client_credentials"
        assert data["scope"] == "read:vat"
        return _FakeResponse(200, {"access_token": "fake-token"})

    def fake_get(url, headers, timeout):
        assert url.endswith("/organisations/vat/check-vat-number/lookup/553557881")
        assert headers["Authorization"] == "Bearer fake-token"
        assert headers["Accept"] == "application/vnd.hmrc.2.0+json"
        return _FakeResponse(200, {
            "target": {
                "name": "Example Fixture Trading Ltd",
                "vatNumber": "553557881",
                "address": {"line1": "1 Test Street", "postcode": "AB1 2CD", "countryCode": "GB"},
                "effectiveDate": "2020-01-15",
            },
            "consultationNumber": "12345",
        })

    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.post", fake_post)
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.get", fake_get)

    result = verifier.verify("553557881")
    assert result.status == VerificationStatus.VERIFIED
    assert result.registered_name == "Example Fixture Trading Ltd"
    assert "1 Test Street" in result.registered_address
    assert result.effective_date == date(2020, 1, 15)
    assert result.verifier_source == "HMRC_API_SANDBOX"
    assert result.raw_response_reference == "12345"


def test_verify_404_maps_to_not_registered(monkeypatch):
    verifier = HmrcVatVerifier("id", "secret", environment="sandbox")
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.post", lambda *a, **k: _FakeResponse(200, {"access_token": "t"}))
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.get", lambda *a, **k: _FakeResponse(404))

    result = verifier.verify("000000000")
    assert result.status == VerificationStatus.NOT_REGISTERED


def test_verify_server_error_maps_to_error_not_silently_dropped(monkeypatch):
    verifier = HmrcVatVerifier("id", "secret", environment="sandbox")
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.post", lambda *a, **k: _FakeResponse(200, {"access_token": "t"}))
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.get", lambda *a, **k: _FakeResponse(500, text="internal error"))

    result = verifier.verify("111111111")
    assert result.status == VerificationStatus.ERROR
    assert "http_500" in result.raw_response_reference


def test_environment_is_always_stamped_in_verifier_source_for_production_too(monkeypatch):
    verifier = HmrcVatVerifier("id", "secret", environment="production")
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.post", lambda *a, **k: _FakeResponse(200, {"access_token": "t"}))
    monkeypatch.setattr("vat_discovery.verification.hmrc_api.requests.get", lambda *a, **k: _FakeResponse(404))

    result = verifier.verify("999999999")
    assert result.verifier_source == "HMRC_API_PRODUCTION"
