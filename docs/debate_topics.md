# Required debate topics

## 1. Could checksum-based enumeration discover VAT numbers?

Technically, a checksum reduces the number of random values worth trying.
Practically, it does not solve the real problem: mapping a valid VAT number to
the right company. Enumeration would still require entity matching at a much
larger scale, and the HMRC API is a gated due-diligence service rather than a
bulk enumeration endpoint.

For that reason, `experiments/hmrc_experiment.py` is deliberately dry-run only.
It accepts a small approved set of candidates, rejects ranges, and makes no
network requests. The project uses public evidence to find a company-specific
candidate first, then verifies it if an authorised verifier is available.

## 2. How would the data stay current?

- Refresh the Companies House snapshot quarterly and compare status, address,
  and incorporation changes.
- Re-run authoritative verification for previously verified VAT numbers on the
  same cycle.
- Re-check a source page sooner when a previously confirmed website becomes
  unreachable or its evidence changes.

The POC observed one site disappearing between checks, so source freshness is
not theoretical. VAT re-verification has not been tested yet because no record
has reached `VERIFIED` status.

## 3. How can wrong data be detected without a full reference dataset?

The project uses several independent checks rather than a single similarity
score: company number, postcode, address, domain, source context, and an
authoritative verifier where available. The POC caught name collisions, claims
that appeared only in search summaries, and address differences that were valid
because the company number matched.

This does not produce a population-wide precision figure. It does show that
direct source retrieval and multiple entity signals catch the errors seen in the
pilot. Production should measure the share of leads rejected after source fetch
and retain those cases as regression fixtures.

## 4. Which sources are suitable for commercial use?

| Source | Position |
|---|---|
| Companies House bulk data | Suitable as the identity backbone, subject to confirming reuse terms. |
| First-party company websites | Suitable for discovery when normal source terms and throttling are respected. |
| Raw search-provider results | Suitable as leads if every claim is independently fetched. |
| HMRC API | Suitable once onboarding and production access are approved. |
| Open-web PDF search | Not shown to be useful in this POC. |
| Third-party VAT directories | Do not use as a primary source; their provenance and freshness are unclear. |
