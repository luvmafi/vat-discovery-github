# Economics

Measure and model costs per 1,000, 10,000, 40,000, and 1,000,000 companies: discovery queries, requests/bandwidth, extraction compute, PDFs/OCR, storage, verification, manual review, and operations. Record actual unit costs during experiments; treat missing inputs as `UNAVAILABLE`, not zero.

Primary measure: `total attributable cost / high-confidence verified VATs`. Also report cost per processed company and cost per verified candidate, with denominator-zero shown as unavailable. Separate observed POC costs from hypothetical scaled estimates and state throughput, cache hit rate, source-access, and review-rate assumptions.

## Status

Computed via `src/vat_discovery/economics/model.py` against `config/economics.yaml` (every input dated, sourced, and tagged with a `basis`). Nothing below is fabricated; every figure is either **observed** in this project's own pilots, a **dated market price** looked up on 2026-08-16, or an explicitly labelled **assumption** not yet validated against real timed data.

## Unit-cost inputs and their basis

| Input | Value | Basis | Source |
|---|---|---|---|
| Search requests per company | 1.214 | **OBSERVED** | `experiments/source_website_round3.py`: 28 companies, 29 search calls + 5 verification fetches = 34 requests |
| Search price | $15.00 / 1,000 queries | **MARKET PRICE** (2026-08-16) | SerpAPI Developer tier (5,000/month) |
| OCR pages per company | 0.0 | **OBSERVED** | OCR has never been triggered in any pilot (`extraction/pdf.py` is TEXT-layer only by design) |
| OCR price | $1.50 / 1,000 pages | **MARKET PRICE** (2026-08-16) | Google Cloud Vision, TEXT_DETECTION |
| Storage per company record | 5 KB | **ESTIMATE** | Rough row-set size; not measured against a populated DB at scale |
| Storage price | $0.023 / GB / month | **MARKET PRICE** (2026-08-16) | AWS S3 Standard, first 50TB tier |
| Manual review time per company | 3.0 minutes | **ASSUMPTION, unvalidated** | Not timed against a real human review session; to be replaced once Phase 10 manual validation actually runs |
| Manual review labor rate | £14.00/hour ($18.90 at 1.35 fx) | **MARKET PRICE** (2026-08-16) | UK Junior Data Analyst/Researcher average, Glassdoor UK |
| HMRC verification cost | $0.00/call | **DOCUMENTED, but access UNAVAILABLE** | Currently free once credentialed; credentials/onboarding not yet obtained |
| Engineering/operations | — | **NOT ESTIMATED** | No defensible unit figure exists yet; deliberately excluded from the total rather than invented |

## Computed cost by scale

| Companies | Total cost | Cost / company | Candidates expected (5.56% observed rate) | Cost / candidate | Cost / **verified** VAT |
|---:|---:|---:|---:|---:|---:|
| 1,000 | $963.21 | $0.9632 | 55.6 | $17.32 | **UNAVAILABLE** |
| 10,000 | $9,632.10 | $0.9632 | 556.0 | $17.32 | **UNAVAILABLE** |
| 40,000 | $38,528.40 | $0.9632 | 2,224.0 | $17.32 | **UNAVAILABLE** |
| 1,000,000 | $963,210.11 | $0.9632 | 55,600.0 | $17.32 | **UNAVAILABLE** |

Cost per company is flat across scale because every modeled input here scales linearly (search requests, storage, manual review) — this model has no economies of scale built in (e.g. bulk API-tier discounts, shared engineering cost amortized over volume) because none of those are observed or defensibly estimated yet. Real production cost per company at 1,000,000 would very likely be lower than this linear extrapolation, not higher, once bulk pricing tiers and amortized engineering cost are factored in — but that would require assumptions this project has no basis for yet, so the model intentionally does not guess at them.

**Cost per candidate found ($17.32) is a real, computable number** — it uses only the observed 5.56% candidate-discovery rate from 36 real piloted companies (`docs/findings.md`). **Cost per high-confidence *verified* VAT is `UNAVAILABLE`, not a number** — this is the single most important line in this table. Zero candidates have ever been run through an authoritative verifier, because no HMRC (or equivalent) credentials exist. This is not a rounding error or a conservative placeholder: it is the literal, current state of the project, and it is the same conclusion the discovery pilots themselves reached (`research_report.md`, Phase 2 round 3) — the binding constraint on this whole pipeline is verifier access, not search cost, storage cost, or discovery signal.

## What would change this table

1. **HMRC verifier credentials** — turns `cost / verified VAT` from `UNAVAILABLE` into a real number for the first time. Nothing else in this table matters commercially until this exists.
2. **A timed manual-review pilot** (Phase 10, 100 companies) — replaces the 3-minutes/company assumption with an observed figure, which could move the manual-review line significantly in either direction.
3. **A real production `SearchProvider` adapter run** — replaces "observed requests per company" (measured from agent-mediated search, not a metered API) with a directly billed, metered figure; likely close to what's modeled here since the request pattern would be similar, but not yet confirmed.
4. **Bulk pricing tiers at scale** — SerpAPI's own pricing drops to ~$9.17/1,000 at its highest published tier; this model conservatively uses the mid tier throughout rather than assume a bulk discount that hasn't been negotiated.
