# UK VAT Identifier Discovery — project closed pending HMRC production access

This repository is an evidence-first local proof of concept for assessing whether UK VAT registration numbers can be responsibly discovered from public evidence. It is **not** a scraper and it performs no live collection by default.

## Phase 0 status

Implemented: architecture, data contracts, SQLite schema, configurable stratification/scoring, deterministic sample-allocation code, source-adapter and verifier interfaces, safe experiment records, and unit-test scaffolding.

## Phase 1 status

Done: ingested the real Companies House 2026-08-01 snapshot (`BasicCompanyDataAsOneFile-2026-08-01.csv`, 5,695,465 rows) via `src/vat_discovery/ingestion/companies_house.py` into `data/intermediate/population.csv` (5,190,464 rows with `CompanyStatus == Active`; manifest at `data/raw/companies_house_snapshot_manifest.json`). Generated the deterministic 500-company sample with `sampling/stratify.py` (seed `20260815`, reference date `2026-08-01`) into `data/processed/sample.csv`; all 50 populated strata are represented with no zero-allocation strata; manifest at `data/processed/sample_manifest.json`.

Note: while building the ingestion module, discovered the real snapshot pads some header names with a leading space (e.g. `" CompanyNumber"`), which is not documented anywhere and silently dropped every row on the first real run (caught because `rows_kept` was 0 — not because it looked plausible). The parser now strips header whitespace; see `tests/test_ingestion.py::test_convert_tolerates_leading_space_padded_header`.

Not implemented: manual review of the sample composition/manifest by a human, PDF collection, live HMRC access, entity-match production decisions, manual-review data, or reported population-level coverage. No results have been fabricated.

## Phase 2 status (pilot, not scaled)

Built `src/vat_discovery/extraction/html.py` (deterministic VAT-candidate extraction from text: keyword-proximity and bare GB-prefix patterns, unit-tested, feeds `normalization.vat`). Ran a small (n=8) company-website discovery pilot on a stratum-spread subset of the sample — see `experiments/source_website.py` and `docs/findings.md`. No credentialed search API exists yet, so the pilot used the operating agent's own search/fetch tools as a documented manual stand-in for the `SearchProvider` adapter, not an automated pipeline run.

**Result: 0/8 confirmed entity-matched websites, 0/8 VAT evidence found.** This is a real, negative pilot result, recorded honestly with full provenance in `data/vat_discovery.sqlite` (`websites`, `source_experiments` tables) — not smoothed over. See `docs/findings.md` for the failure-mode breakdown and `research_report.md` for the narrative. Conclusion so far: NO-GO for a single-query search strategy specifically; company websites as a source remain an open question pending a larger, multi-query pilot.

**Round 2 retest** (`experiments/source_website_round2.py`): same 8 companies, disambiguated query (town + sector keyword from the real Companies House record) instead of a generic query. Result: still 0 new confirmed websites, 0 new VAT evidence — but 1 additional real wrong-entity near-miss caught (MEAT AND SHAKES (PRESTON) LIMITED, a differently-numbered company than our sampled MEAT N SHAKE LTD). This strengthens rather than weakens the round-1 NO-GO for this population segment.

**Round 3 extended pilot** (`experiments/source_website_round3.py`, n=28 new, 36 distinct companies cumulative): produced this project's **first two real, first-party-confirmed VAT candidates** (HILLS FAMILY LTD, JTHN LIMITED — both found in their own website footers, both with exact Companies House company-number matches). Both were run through the actual pipeline code (extraction → normalization/checksum → entity resolution) and both correctly land at **TIER_3**, because `verification_status` is honestly `UNAVAILABLE` (no HMRC credentials exist) and the scorer refuses to rate anything TIER_1 without authoritative verification — the Phase-0 design working as intended on real data for the first time. Also surfaced two important findings: (1) JTHN's VAT number fails our checksum validator despite strong corroborating evidence — flagged as a validator-coverage gap, not resolved by loosening the check; (2) a third claimed VAT number (AQUAWASH LIMITED) appeared in a search-tool summary but was **not actually present** on the cited page when fetched directly — rejected, and documented as a distinct "search-summary hallucination" failure mode that any production pipeline must guard against by extracting from raw fetched text, never trusting a summary. **Revised conclusion: CONDITIONAL GO for company-website discovery — the source has real, non-zero signal (~5.6% of 36 companies); the binding constraint is now the missing authoritative verifier, not discovery itself.**

## Phase 4 status (pilot, not scaled)

Built `src/vat_discovery/extraction/pdf.py` (TEXT-layer-only extraction via `pypdf`; no default OCR; page-level text-presence stats recorded to surface OCR need without acting on it), unit-tested against synthetic fixtures generated with `fpdf2` (`tests/test_extraction_pdf.py`). Piloted public-PDF discovery (`"<company name>" filetype:pdf VAT`) against the same 8 companies as the Phase 2 pilot, for direct comparability — see `experiments/source_pdf.py`.

**Result: 0/8 company-specific PDFs found at all.** The PDF extractor has therefore not yet been run against a real document. Recorded in `data/vat_discovery.sqlite` and `docs/findings.md`. Conclusion so far: NO-GO for `filetype:pdf` open-web search alone on this sample; next step is either a multi-query website retest (Phase 2, the more promising source so far) or a targeted test against Companies House's own filed-accounts PDFs.

## Phase 8 status (entity resolution, code only — no live candidates to score yet)

Built `src/vat_discovery/entity_resolution/scoring.py`: multi-signal scoring (name/address/postcode/domain/company-number/context) against the weights and tiers already defined in `config/scoring.yaml` from Phase 0. Every signal is independently inspectable via `MatchResult.explanation`; an unverified candidate can never exceed TIER_3 regardless of score, matching the brief's "no VAT is found without authoritative verification" rule.

Tested against 32 cases including two **real regression fixtures drawn directly from the Phase 2 pilot's wrong-entity near-misses** (KNOTAGAIN INTERNATIONAL LTD vs. the unrelated South African retailer; MEAT N SHAKE LTD vs. the differently-numbered MEAT AND SHAKES (PRESTON) LIMITED) — both correctly fail to reach TIER_1. Not yet exercised on a real candidate end-to-end, since no pilot so far has produced one; it is ready for the moment one does.

## Phase 10 status (manual validation, complete — 100/100)

Selected the deterministic 100-company manual-validation subset from the 500-company sample (`src/vat_discovery/sampling/manual_validation_subset.py`, seed `20260816`, distinct from the main sample seed; 42 of 50 strata represented, none artificially boosted). Manifest at `data/processed/manual_validation_subset_manifest.json`.

**Labelling note, important:** the brief specifies independent *human* manual review, precisely to catch failure modes the automated pipeline cannot see on its own. These reviews were performed by the operating agent using the same tools as the Phase 2 pilots, at the user's explicit request. Every row is recorded with `reviewer = AGENT_ASSISTED_NOT_INDEPENDENT_HUMAN_REVIEW` in `manual_reviews` — never to be read later as satisfying the brief's original human-review requirement.

**Result: 6/100 companies (6%) produced a real, first-party-confirmed VAT candidate**, all run through the actual pipeline and stored with full provenance: HILLS FAMILY LTD, JTHN LIMITED, GO2 PROPERTY SERVICES LIMITED, G A PLANT AND TOOL HIRE LTD, TTG PORTSMOUTH LIMITED, BULLET BUILDING PRODUCTS LIMITED. Every one is capped at TIER_3 — not from weak evidence (one scores 0.96/1.0) but because no HMRC credentials exist to authoritatively verify any of them. Two more findings worth flagging on their own:

- **A checksum-validator bug found and fixed.** Three of the six real candidates initially failed `validate_uk_vat_syntax` under both implemented rules despite exact company-number corroboration. Root cause: a sign error in the "9755" legacy-variant formula (`standard + 42` instead of the correct `42 - standard`). Fixed in `src/vat_discovery/normalization/vat.py`, with regression tests using the three real numbers in `tests/test_normalization.py`. Unfixed, this would have silently misclassified most real UK VAT numbers using this check scheme as invalid.
- **Two more hallucinated/unconfirmable search claims caught** (FIREBIRD MUSIC LIMITED, BRISTOL ENERGY & TECHNOLOGY SERVICES), bringing the total to 4 rejected claims out of ~10 investigated this project (~40% false-claim rate before independent verification) — reinforcing that search-result summaries must never be trusted as evidence without fetching and reading the actual source.

Full detail in `docs/findings.md` and `research_report.md`.

## Phase 12 status (economics, code + first computed pass)

Built `src/vat_discovery/economics/model.py` against `config/economics.yaml` — every unit-cost input tagged with its basis (observed from this project's own pilots / dated market price / explicit unvalidated assumption). Computed cost tables at 1,000/10,000/40,000/1,000,000 companies in `docs/economics.md`. Headline finding: **cost per candidate found is a real, computable $17.32; cost per high-confidence *verified* VAT is `UNAVAILABLE`**, not a number — because zero candidates have ever been run through an authoritative verifier. This is the same conclusion the discovery pilots reached independently: verifier access, not discovery or search cost, is the binding constraint.

## Local database

```powershell
sqlite3 data\vat_discovery.sqlite ".read sql\schema.sql"
.\.venv\Scripts\python.exe -m vat_discovery.ingestion.load_sample data\processed\sample.csv
.\.venv\Scripts\python.exe experiments\source_website.py
.\.venv\Scripts\python.exe experiments\source_pdf.py
```

## Local setup

Requires Python 3.11+.

```powershell
cd vat-discovery
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
python -m vat_discovery.sampling.stratify --help
```

Create the local database with `sqlite3 data/vat_discovery.sqlite ".read sql/schema.sql"`, or execute the schema through any SQLite client. Copy `.env.example` to `.env` only when an approved verifier is ready; it is intentionally unused in Phase 0.

## Architecture and contracts

`Companies House input → canonical company → stratified sample → source adapters → evidence-bearing VAT candidates → syntax filter → verifier → entity match → confidence decision → provenance-backed result`.

Every stage exchanges typed records in `src/vat_discovery/contracts.py`. Raw values and evidence are retained; a checksum result is a filter, never verification. The database treats Companies House number and VAT number as different identifiers.

The only runnable HMRC-related scaffold is a dry-run economics recorder. It rejects ranges and live requests by design. A future authenticated verifier must implement `VatVerifier` and comply with HMRC terms/rate limits.

## Deterministic sampling design

The planned population is active UK companies from Companies House. Companies are assigned to an explicit SIC category and incorporation-age bucket, then allocated proportionally across their combined stratum using largest-remainder allocation. Within each stratum selection is deterministic using `sample_seed`; `sample_weight = population_count / sample_count` is retained. Sparse strata are not artificially boosted.

Input for the sampler is a CSV with at least `companies_house_number`, `raw_company_name`, `company_status`, `sic_codes`, and `incorporation_date`. See the sampler help for commands. The source population snapshot, query/version, as-of date, and seed must be recorded before Phase 1.

## Guardrails

- No candidate is a successful discovery without evidence, authoritative verification, entity association, and provenance.
- No absence of web evidence is treated as non-registration.
- Source experiments must write an experiment record with sample, configuration/code version, observed results, and failures.
- Live collection is opt-in and must respect robots, terms, throttling, caching, and `Retry-After`.
- The HMRC API is a candidate verifier only after credentials/onboarding; its current documentation says it requires authentication and is for trader due diligence. See the [HMRC API documentation](https://developer.service.hmrc.gov.uk/api-documentation/docs/api/service/vat-registered-companies-api/2.0).

## Phase 1 entry criteria

Obtain and document a Companies House population snapshot and its permitted acquisition method; confirm active-status/SIC/date fields; generate the 500-company sample; and save its manifest. Then run one small, documented source-accessibility experiment before building a crawler.

To ingest a manually downloaded snapshot:

```powershell
python -m vat_discovery.ingestion.companies_house `
  data\raw\BasicCompanyDataAsOneFile-2026-08-01.csv `
  data\intermediate\population.csv `
  --snapshot-date 2026-08-01
```

This writes `data/intermediate/population.csv` (the sampler's input format) and `data/raw/companies_house_snapshot_manifest.json` (source URL, snapshot date, row counts, status distribution). The actual snapshot file must be downloaded by hand from the Companies House bulk-data page first; it is not fetched automatically.

## HMRC verification status

**Sandbox integration built and live-tested; production access not yet obtained.** A Sandbox application was registered on the HMRC Developer Hub (Sandbox credentials are issued instantly). `src/vat_discovery/verification/hmrc_api.py` implements a real `HmrcVatVerifier` (OAuth 2.0 client_credentials, `GET /organisations/vat/check-vat-number/lookup/{vrn}`) against HMRC's actual published API spec, and `experiments/hmrc_sandbox_test.py` successfully called HMRC's live Sandbox server using one of HMRC's own published test VRNs — a real network round-trip, real OAuth token, real response, correctly parsed. Sandbox only ever returns HMRC's own mock data, never real company data, and the script explicitly refuses to run unless `HMRC_ENVIRONMENT=sandbox` is set — as a guard against ever pointing this at production without deliberate reconfiguration.

**Production credentials were not applied for** — that step needs the ~2-week HMRC approval process, which was out of this project's window (see `docs/decision.md`). None of this touches or is confused with the 6 real candidates already found; they remain unverified until production access exists. Also finished: `src/vat_discovery/verification/test_fixture.py` + `experiments/pipeline_demo_dry_run.py` (fictional end-to-end demo reaching TIER_1) and `entity_resolution/conflicts.py` (brief section 18's previously-unbuilt conflict-handling logic).

The moment production credentials exist: change `HMRC_ENVIRONMENT` to `production` in `.env`, point `HmrcVatVerifier` at the real candidates found — no further code changes needed.

## Round 4 (deadline-driven extension)

30 more companies piloted (`experiments/source_website_round4.py`), pushing cumulative distinct companies piloted past 160. **1 more real candidate found: EXECUTOURS LIMITED** — exact company-number/address match, VAT confirmed on its own site. **Cumulative: 7 of ~160 companies (≈4.4%)** have produced a real, first-party-confirmed VAT candidate across this project. EXECUTOURS' VAT number also fails both implemented checksum rules (the 4th of 7 real candidates to do so) — flagged as an open follow-up on `normalization/vat.py`'s checksum coverage, not guessed at further without a confirmed-correct third algorithm.

## Decision

**CONDITIONAL GO** — see [decision.md](docs/decision.md) for the full evidence trace. Discovery, extraction, normalization, and entity resolution are all built, tested, and have processed real data; the single binding constraint is the absence of an authoritative VAT verifier (HMRC credentials or equivalent). See also [debate_topics.md](docs/debate_topics.md) (the brief's four required debate topics, answered with evidence), [production_architecture.md](docs/production_architecture.md) (what a scaled version needs, driven by what actually broke in this POC), and [germany_comparison.md](docs/germany_comparison.md) (optional; the UK pipeline's discovery/extraction stages would transfer, its population-acquisition strategy would not).

Detailed design: [methodology.md](docs/methodology.md), [source_matrix.md](docs/source_matrix.md), [findings.md](docs/findings.md), [economics.md](docs/economics.md), [appendix.md](docs/appendix.md), and [research_report.md](research_report.md).
