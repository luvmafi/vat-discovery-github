"""Real network call to HMRC's Sandbox "Check a UK VAT Number" API v2, using
one of HMRC's own published test VRNs (from their public GitHub test-data
list, not invented here). This is the first live call to HMRC in this
project.

CRITICAL: Sandbox returns HMRC's own mock/test data only -- never real
company data, regardless of which VRN is queried. This script exists to
prove the OAuth + HTTP integration in hmrc_api.HmrcVatVerifier actually
works against a real HMRC server, not to verify any real candidate. Every
one of this project's 6 real candidates remains unverified until production
credentials exist (see docs/decision.md); this script must never be pointed
at them while HMRC_ENVIRONMENT=sandbox.
"""
from __future__ import annotations

import json
from pathlib import Path

from vat_discovery.verification.hmrc_api import HmrcVatVerifier

# From HMRC's own sandbox test-data file:
# https://github.com/hmrc/vat-registered-companies-api/blob/main/public/api/conf/2.0/test-data/vrn.csv
HMRC_PUBLISHED_TEST_VRN = "553557881"


def load_env(path: Path = Path(".env")) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def main() -> None:
    env = load_env()
    environment = env.get("HMRC_ENVIRONMENT", "sandbox")
    if environment != "sandbox":
        raise SystemExit(
            f"Refusing to run: HMRC_ENVIRONMENT is {environment!r}, expected 'sandbox'. "
            "This script is for sandbox integration testing only."
        )

    verifier = HmrcVatVerifier(
        client_id=env["HMRC_CLIENT_ID"],
        client_secret=env["HMRC_CLIENT_SECRET"],
        environment=environment,
    )
    result = verifier.verify(HMRC_PUBLISHED_TEST_VRN)

    print("=== HMRC SANDBOX INTEGRATION TEST (mock data, not a real company) ===")
    print(json.dumps({
        "vat_number_queried": result.vat_number,
        "status": result.status.value,
        "registered_name": result.registered_name,
        "registered_address": result.registered_address,
        "effective_date": result.effective_date.isoformat() if result.effective_date else None,
        "verifier_source": result.verifier_source,
        "raw_response_reference": result.raw_response_reference,
    }, indent=2))


if __name__ == "__main__":
    main()
