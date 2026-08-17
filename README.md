# UK VAT Identifier Discovery

A local research proof of concept for finding possible UK VAT registration
numbers from public evidence, then verifying that the number belongs to the
right company. It is deliberately evidence-first: a number found on a website
is a candidate, not a completed result.

**Current decision: CONDITIONAL GO.** Company websites provide a useful signal,
but the project needs an authoritative VAT-verification route before it can
produce a reportable dataset. See [the decision](docs/decision.md) for the
full rationale.

## What we learned

The project started from a real Companies House snapshot dated 2026-08-01:
5.19 million active companies. From that population it created a reproducible,
stratified sample of 500 companies and a 100-company validation subset.

Across the discovery work completed so far, 7 of roughly 160 companies (about
4.4%) produced a VAT candidate with first-party website evidence. The six
candidates found in the 100-company subset correspond to a 6% rate in that
subset. None has been authoritatively verified, so every one remains TIER_3
(`CANDIDATE_ONLY_NOT_A_DISCOVERY`).

| Area | Result |
|---|---|
| Company websites | A real, non-zero discovery signal; 7 first-party candidates found so far. |
| Open-web PDF search | No useful evidence in the small pilot; not a viable standalone source. |
| Entity resolution | Correctly rejected real same-name and wrong-entity near misses. |
| HMRC verification | Sandbox integration works; production credentials have not yet been requested. |

The work also found a practical failure mode worth keeping: around 4 of roughly
10 VAT claims surfaced in search summaries did not hold up when the underlying
page was fetched. The pipeline therefore treats search results as leads only
and records evidence from the source document itself.

## What is in the repository

- Ingestion of Companies House data and deterministic stratified sampling.
- VAT extraction from HTML and PDF text, normalisation, and checksum checks.
- Explainable entity matching using name, address, postcode, domain,
  company number, and context signals.
- SQLite storage for source documents, candidates, matches, verifications, and
  experiment records.
- An HMRC VAT verifier adapter, tested end to end against the HMRC Sandbox.
- Tests and experiments that reproduce the recorded pilot work.

The project does not run live collection by default. A production collector
would still need a proper search provider, source-specific terms and robots
handling, throttling, caching, and retry controls.

## Important limits

- **No VAT number is verified yet.** The HMRC Sandbox returns test data only.
  Production credentials need to be requested and approved before the existing
  candidates can be checked against real data.
- **The discovery rate is an early estimate, not a forecast.** The pipeline has
  not been exercised at the customer's 40,000-supplier scale.
- **The 100-company validation subset was agent-assisted, not independently
  reviewed by a human.** It is recorded as such and does not replace the human
  review requested in the original brief.
- **A checksum is not verification.** It is used as a diagnostic filter; the
  project found and fixed one real checksum implementation bug during the
  pilot.

## Run locally

Requires Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

The local database is `data/vat_discovery.sqlite`. To create it from the
schema:

```powershell
sqlite3 data\vat_discovery.sqlite ".read sql\schema.sql"
```

To ingest a Companies House snapshot that has already been downloaded locally:

```powershell
python -m vat_discovery.ingestion.companies_house `
  data\raw\BasicCompanyDataAsOneFile-2026-08-01.csv `
  data\intermediate\population.csv `
  --snapshot-date 2026-08-01
```

## Documentation

- [Decision](docs/decision.md) — the evidence behind the CONDITIONAL GO verdict.
- [Findings](docs/findings.md) — pilot results, candidates, and rejected claims.
- [Methodology](docs/methodology.md) — sampling, evidence, and validation design.
- [Source matrix](docs/source_matrix.md) — sources tested and their outcomes.
- [Production architecture](docs/production_architecture.md) — what a scaled implementation would need.
- [Economics](docs/economics.md) — assumptions and cost model.
- [Research report](research_report.md) — longer narrative of the project.

## Next step

Request HMRC production credentials, then verify the existing TIER_3 candidates
with the implemented verifier. That will show whether the discovery signal can
be converted into reliable, reportable VAT identifiers.
