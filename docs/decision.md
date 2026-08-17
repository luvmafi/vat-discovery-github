# Decision

## Verdict: CONDITIONAL GO

The discovery approach is promising enough to continue, but it cannot yet
produce a reliable VAT dataset. The missing piece is an authoritative verifier:
HMRC production access or a documented equivalent.

## Why this is not a GO yet

Seven VAT candidates have been found with first-party website evidence, but
none has been checked against live HMRC data. Under this project's rules, an
unverified number stays at TIER_3 (`CANDIDATE_ONLY_NOT_A_DISCOVERY`), even when
the company-number and address evidence is strong. A commercial output needs
verified identifiers, not plausible-looking numbers.

The HMRC adapter is implemented and was tested against the live Sandbox,
including OAuth and a lookup response. Sandbox data is test data only.
Production credentials have not been requested; that onboarding step was outside
the assessment window.

## Why this is not a NO-GO

- The website signal is real: 7 of roughly 160 companies tested produced a
  first-party VAT candidate. In the 100-company validation subset, 6 candidates
  were found.
- Entity matching handled the difficult cases seen in the pilot: two name
  collisions were rejected, while two genuine candidates with a different
  website address were retained because their company numbers matched.
- The work exposed useful failure modes rather than hiding them. Four VAT claims
  from search summaries did not survive a direct source check, and a checksum
  implementation bug was found and fixed using real candidates.
- The population, sampling method, evidence records, and experiments are
  reproducible from the repository.

These are enough to justify the next investment. They are not enough to claim
that the pipeline already produces verified VAT identifiers.

## What happens next

1. Request HMRC production credentials, then run the existing seven candidates
   through `HmrcVatVerifier`.
2. Replace the agent-mediated discovery work with a metered `SearchProvider` and
   run a larger sample to narrow the discovery-rate estimate.
3. Repeat the 100-company validation with an independent human reviewer and
   capture the time required for review.

No code change should be needed for the first step beyond production
configuration and credentials. Candidates that HMRC verifies and that meet the
entity-resolution rule can move to TIER_1.

## When to stop

Revisit this decision if either of these happens:

- HMRC access is not available and no acceptable verifier can be used instead;
  in that case the product cannot move beyond TIER_3 candidates.
- A larger, production-style discovery run shows that the observed 4–6% website
  discovery rate was an optimistic small-sample result.

The current rate is a planning input, not a forecast that 40,000 suppliers will
produce a fixed number of verified VAT records.
