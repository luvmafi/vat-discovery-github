# Production architecture

This describes what a scaled version of this pipeline would need to look like, based on what actually broke, was slow, or was risky during this POC — not a generic microservices diagram. Per the brief's own rule (section 44): nothing here is recommended unless a real bottleneck in this project motivates it.

## Pipeline shape (unchanged from the POC's design, still correct at scale)

```
Companies House bulk snapshot (monthly, manual download)
        |
   ingestion.companies_house  ->  population.csv (streamed, no memory blowup even at 5.7M rows)
        |
   sampling.stratify  ->  deterministic sample + manifest
        |
   discovery (website search)  ->  candidate domains, CONFIRMED/AMBIGUOUS/REJECTED
        |
   extraction (HTML/PDF text)  ->  raw candidate + context + provenance
        |
   normalization.vat  ->  normalized value + syntax/checksum filter (never proof)
        |
   VatVerifier (HMRC, currently UNAVAILABLE)  ->  VERIFIED / NOT_REGISTERED / ERROR
        |
   entity_resolution.scoring  ->  TIER_1/2/3 + explanation
        |
   TIER_1  ->  reportable dataset row        TIER_2/3  ->  manual review queue
```

Nothing about this shape needs to change for scale. What needs to change is *how* each stage runs, and that's driven by three concrete things this POC actually hit.

## What actually broke or was slow in this POC (the only justified scale-up drivers)

1. **`sampling.manual_validation_subset` and `stratify` load the full population into memory as Python dicts.** At 5.19M active companies this worked (seconds, a few hundred MB), but it will not work unmodified at a hypothetical multi-country, tens-of-millions-of-companies population. This is the first real bottleneck, and the only one this POC actually measured: everything else below is anticipated, not observed.
2. **Website/search discovery is currently one HTTP-ish request per company via the operating agent's own tools**, not a real rate-limited, cached, robots.txt-aware crawler. At 40,000 suppliers (the customer's actual scale) this is roughly 40,000-50,000 requests at the observed 1.214 requests/company ratio (`config/economics.yaml`) — feasible for a real HTTP client with domain-level throttling and caching, not feasible run manually.
3. **Every entity-resolution false-positive this POC found (KNOTAGAIN, MEAT AND SHAKES (PRESTON), the 4 hallucinated VAT claims) was caught by a human-in-the-loop re-check**, not by an automated gate. At 40,000+ companies, nobody is going to manually re-fetch every candidate's source page the way this POC did for all 6 real candidates found.

## What that implies, concretely

- **Population/sampling**: swap the in-memory list for a streaming/chunked approach (or just a real database — SQLite is already the target; loading via `INSERT` in a stream instead of building Python lists first) once population size stops comfortably fitting in memory. Not needed yet at UK-only scale; would matter for a multi-country population.
- **Discovery**: replace the agent-mediated search used throughout this POC with a real `SearchProvider` implementation (the interface already exists in `discovery/base.py`, unused until credentials exist) behind a rate-limited, cached, robots.txt-respecting HTTP client — the guardrails already written into `README.md`/`config/settings.yaml` (`requests_per_domain_per_minute`, caching) were designed for exactly this and have not yet been exercised against a real scaled run.
- **Verification**: this is the actual hard constraint, not a scaling problem — see `docs/economics.md` and `research_report.md` Phase 10. No architecture change fixes missing HMRC credentials.
- **False-positive containment at scale**: the automated `entity_resolution.scoring` TIER_1/2/3 split already routes ambiguous cases to manual review instead of auto-accepting them (`config/scoring.yaml`'s `required_for_high_confidence` gate) — this is the mechanism that has to carry the load a human re-checker carried in this POC. The manual-review queue itself (`manual_reviews` table) exists in schema but has no actual UI/workflow tooling built; that is a real production gap, not yet a bottleneck because volume has been small.

## Monitoring (what to actually watch, not a generic list)

Driven by real POC findings, in priority order:

1. **Search-summary/LLM-mediated-evidence contamination rate** — this POC found roughly 40% of raw VAT-number claims surfaced by search-result summaries did not hold up under direct source verification (`docs/findings.md`, Phase 10). Any production discovery path that uses an LLM to summarize search results (as this POC's pilots did, out of necessity) needs this rate tracked per batch; a real `SearchProvider` adapter returning raw snippets instead of summaries should reduce this to near zero, and that reduction itself is worth confirming, not assuming.
2. **Checksum-validator false-rejection rate** — this POC found a live sign-error bug that rejected real VAT numbers (`normalization/vat.py`, fixed after 3 of 6 real candidates initially failed it). A checksum validator is exactly the kind of code that looks correct until tested against real registered numbers; any future change to it should be re-validated against a held-out set of confirmed-real VAT numbers before deployment, not just synthetic test cases.
3. **VAT deregistration / company dissolution / address changes** (brief section 43) — not yet observed in this POC (no verified records exist yet to go stale), but the schema already separates `discovered_at` from `verified_at` specifically so staleness is measurable once real verified records exist.
4. **Source discovery rate drift** — the observed ~5-6% company-website discovery rate (Phase 2 + Phase 10 combined, `docs/findings.md`) is a real baseline. A production run should alert if the rate drops meaningfully below that on a comparable stratified sample, since that would signal either a broken discovery adapter or a genuine change in the population's web presence, and those need different responses.

## Refresh cycle

Quarterly is the chosen default (per the brief), sized to what changes slowly (company formation/dissolution, VAT deregistration) rather than what changes fast (nothing in this pipeline changes fast — search index content and website availability drift, but not fast enough to need daily refresh). The one thing this POC found that argues for *faster-than-quarterly* handling: a domain found in one Phase 2 round (CHURCHGATE WOKING LTD's candidate site) no longer resolved by the time it was re-checked — website availability itself is not stable even within a single project session, let alone a quarter. Production should treat a previously-CONFIRMED website going unreachable as an event-driven re-check trigger, not wait for the next quarterly cycle.

## What this POC deliberately does not tell you

- **Nothing here has been run at real production scale.** The largest single population operation (ingesting 5.19M active companies) worked fine; the largest *discovery* operation (130 distinct companies across all pilots) is roughly 0.3% of the customer's 40,000-supplier target. Extrapolating discovery-pipeline behavior from 130 companies to 40,000 is not validated by this POC — it is a reasonable next step, not a conclusion already reached.
- **No cost has been observed at scale**, only modeled from unit prices and observed per-company ratios (`docs/economics.md`). The economics model explicitly separates observed-ratio-times-market-price from untested assumptions for this reason.
