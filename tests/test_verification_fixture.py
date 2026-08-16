from vat_discovery.contracts import VerificationStatus
from vat_discovery.verification.test_fixture import TestFixtureVerifier


def test_verify_known_fixture_returns_verified():
    result = TestFixtureVerifier().verify("123456715")
    assert result.status == VerificationStatus.VERIFIED
    assert result.registered_name == "EXAMPLE FIXTURE BUILDERS LTD"
    assert result.verifier_source == "TEST_FIXTURE"


def test_verify_known_not_registered_fixture():
    result = TestFixtureVerifier().verify("999999999")
    assert result.status == VerificationStatus.NOT_REGISTERED
    assert result.registered_name is None


def test_verify_unknown_number_is_unavailable_not_invented():
    result = TestFixtureVerifier().verify("111111111")
    assert result.status == VerificationStatus.UNAVAILABLE
    assert result.registered_name is None
    assert result.raw_response_reference is None
