# Decision

## Verdict: CONDITIONAL GO

Conditional specifically on obtaining an authoritative VAT verification path (HMRC credentials or an equivalent documented mechanism). This is not a hedge — it is the literal, evidence-backed bottleneck this project identified, distinct from every other question the brief asked.

## Why not a plain GO

No VAT number has ever been verified by this project. Six real, first-party-confirmed candidates exist (`docs/findings.md`, Phase 10) — including one (G A PLANT AND TOOL HIRE LTD) that scores 0.96 out of 1.0 on every non-verification signal in the entity-resolution model — and every one of them is correctly capped at TIER_3, "candidate only, not a discovery," by the project's own design. A dataset with zero verified rows cannot be called GO regardless of how promising the discovery signal looks, because the customer's actual need (a stable identifier linking invoices, records, and tax filings) requires the verification step, not just a plausible-looking candidate.

## Why not NO-GO

Every question that *can* be answered without HMRC access has a real, evidence-backed positive answer:

- **Discovery signal is real and non-trivial.** 6 of 100 companies in an unbiased, stratified, deterministic sample (Phase 10) produced a genuine VAT candidate found on the company's own website — not 0%, not a rounding error, and not cherry-picked (the subset was drawn the same way the main 500-company sample was, proportionally across strata).
- **Entity resolution correctly separates real matches from near-misses.** Two real wrong-entity traps (KNOTAGAIN, MEAT AND SHAKES (PRESTON)) and two address-mismatched-but-genuine matches (JTHN, GO2) were all classified correctly by the same scoring model, using the same fixed thresholds, without needing a separate rule for each case.
- **Precision under scrutiny is defensible.** Roughly 4 of ~10 total VAT-number claims surfaced during this project were caught as unconfirmed or hallucinated *before* being recorded, because every claim was independently re-verified against a primary source rather than trusted at face value. That is the discipline a commercial pipeline needs, and this project demonstrated it works, not just that it's a good idea.
- **The population and sampling methodology is sound and reproducible.** A real 5.19M-row Companies House snapshot, a documented deterministic sampling method, and a documented deterministic manual-validation subset — nothing here is a placeholder.
- **A real bug was caught by real data, not missed.** The checksum-validator sign error would have silently misclassified most real UK VAT numbers using the 9755 check scheme — caught because real candidates contradicted the code, and fixed with regression tests grounded in real numbers.

None of that is undermined by the missing verifier. It means the *rest* of the pipeline is trustworthy enough to build on, once verification exists.

## What GO requires from here

1. **HMRC API credentials/onboarding** (or a documented equivalent authoritative check) — the single blocking item. Nothing else in this list matters commercially until this exists.

   **Status at project close**: a Sandbox application was registered on the HMRC Developer Hub (Sandbox credentials are issued instantly, no approval wait) and a real `HmrcVatVerifier` adapter (`src/vat_discovery/verification/hmrc_api.py`) was built and successfully tested against HMRC's live Sandbox environment — a real OAuth 2.0 client_credentials token exchange and a real `GET` call to `test-api.service.hmrc.gov.uk`, returning HMRC's own mock data (`experiments/hmrc_sandbox_test.py`). This proves the integration works end-to-end against a real HMRC server, not just in theory. **Production credentials were not applied for** — that step still requires the ~2-week approval process and was out of this project's window. Sandbox data is HMRC's own mock/test data and was never applied to any of this project's 6 real candidates; `experiments/hmrc_sandbox_test.py` explicitly refuses to run unless `.env`'s `HMRC_ENVIRONMENT` is set to `sandbox`, as a deliberate guard against accidentally pointing an unapproved credential at the production endpoint.

2. **Re-run the 6 existing TIER_3 candidates through a real verifier** the moment credentials exist — this is nearly free (6 API calls) and would immediately produce this project's first TIER_1 result if even a few come back VERIFIED.
3. **Scale the discovery pilot past n=130** using a real `SearchProvider` adapter (not agent-mediated search) to get a tighter confidence interval on the ~5-6% discovery rate, and to eliminate the hallucination-vs-real-evidence problem structurally rather than by manual re-checking every claim.
4. **A timed Phase 10 re-run** (or equivalent) with an actual independent human reviewer, not agent-assisted, to validate that the ~5-6% rate and the false-claim rate hold up under review that isn't subject to the same tool limitations as the discovery pipeline itself.

## What was finished instead, to leave the pipeline ready for the moment production access arrives

Since real HMRC production verification could not be exercised in this project's window, the remaining engineering risk was closing everything so that production credentials are the only missing input, not credentials-plus-more-engineering:

- **`verification/test_fixture.py`** — a controlled `VatVerifier` implementation against a small, clearly fictional registry (brief section 13 explicitly names "controlled test fixture" as a valid `VatVerifier` implementation alongside the real HMRC API). Never applied to any real candidate.
- **`experiments/pipeline_demo_dry_run.py`** — runs one fictional company through every stage (extraction → normalization → verification → entity resolution) and confirms it reaches TIER_1 end-to-end using the test fixture. Proves the mechanism is wired correctly independent of any real API.
- **`verification/hmrc_api.py`** — a real `HmrcVatVerifier` implementing OAuth 2.0 client_credentials against HMRC's actual endpoints (confirmed from HMRC's own published OpenAPI spec, not guessed), successfully tested against HMRC's live Sandbox server (`experiments/hmrc_sandbox_test.py`) using one of HMRC's own published test VRNs. This is the same code that will call the real production API — only the `environment` parameter and credentials change.
- **`entity_resolution/conflicts.py`** — brief section 18's conflict-handling requirement, previously only a schema table with no logic behind it. Checked against the 6 real candidates: zero conflicts exist in the real data currently.

The result: the moment production credentials exist, changing `HMRC_ENVIRONMENT` from `sandbox` to `production` in `.env` and pointing `HmrcVatVerifier` at the 6 existing candidates is the only remaining step to produce this project's first real TIER_1 result — no further code changes are needed.

## What would change this to NO-GO

- If HMRC access is confirmed unattainable (commercially, legally, or practically) with no equivalent alternative verifier identified, the entire pipeline produces TIER_3 candidates indefinitely — that is not a viable commercial dataset regardless of discovery-rate quality, and the verdict would move to NO-GO at that point, not stay CONDITIONAL indefinitely.
- If a larger-n website-discovery pilot (item 3 above) shows the 5-6% rate was a small-sample artifact and the true rate is much lower, the cost-per-candidate economics (`docs/economics.md`, currently $17.32 at the observed rate) would need re-examination against the customer's actual per-record value threshold.

## What this verdict is not

It is not a claim that 40,000 suppliers will yield ~2,400 verified VATs (40,000 × 6%). The 6% rate is observed on a sample stratified the same way as the population, which supports treating it as a reasonable planning estimate — but it has not been tested at anywhere near that scale, and `docs/production_architecture.md` says so explicitly. This verdict is about whether the *approach* is sound enough to invest further in, not a forecast of the final dataset's size.
