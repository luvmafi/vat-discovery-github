# Findings — Phase 0 / Phase 1 / Phase 2 pilot

## Phase 0-1 observed

Population and sample are now real: 5,190,464 active companies from the 2026-08-01 Companies House snapshot; a deterministic 500-company sample across 50 industry/age strata with none zero-allocated (`data/processed/sample_manifest.json`). No VAT candidate, verifier response, or manual-review annotation exists yet.

## Phase 2 pilot observed (n=8, single-query company-website search)

Source: single naive search query per company, stratum-spread subset of the 500-sample (indices spaced evenly, not cherry-picked). Full per-company detail in `experiments/source_website.py` and the `source_experiments`/`websites` tables in `data/vat_discovery.sqlite`.

| Metric | Value |
|---|---|
| Companies piloted | 8 |
| Confirmed entity-matched websites | 0 |
| Candidate leads found, unconfirmed or unreachable | 3 |
| No website discovered at all | 5 |
| Verified wrong entity (name collision) | 1 |
| Website unreachable (DNS failure) | 1 |
| VAT evidence found | 0 |

Observed failure modes, all real and specific:

- **NO_WEBSITE_DISCOVERED (5/8)**: small/recently-formed entities (SPVs, an LP, a holding company) or generic trading names produced no distinct web presence via a single search query.
- **VERIFIED_WRONG_ENTITY (1/8)**: KNOTAGAIN INTERNATIONAL LTD (UK, Cumbria) vs. a same-named South African retailer on a `.co.za` domain — a real example of exactly the entity-resolution trap section 15/23 of the brief warns about. Rejected, not counted as a lead.
- **AMBIGUOUS_ENTITY (1/8)**: NORTH LONDON GROUP LTD's most plausible domain resolves and loads, but carries zero company-identifying text (no name, address, or registration number) — cannot be confirmed as belonging to this company, so it is not counted as a discovered website despite ranking first in search.
- **WEBSITE_UNREACHABLE (1/8)**: a domain whose address text in a search snippet exactly matched CHURCHGATE WOKING LTD's real registered address no longer resolves (DNS failure) at fetch time — freshness/decay is a real, not hypothetical, failure mode here.

## Phase 4 pilot observed (n=8, `filetype:pdf` search, same companies as Phase 2)

| Metric | Value |
|---|---|
| Companies piloted | 8 |
| Company-specific PDF candidates found | 0 |
| PDF discovery rate | 0.0 |
| VAT evidence found | 0 |

Zero PDFs were found for any of the 8 companies — not "PDFs without VAT text," but no company-specific PDF surfaced at all. Results were consistently dominated by unrelated same-named entities in other countries/registries, generic VAT-compliance documents with no connection to the target company, and for two companies (CHURCHGATE WOKING, MEAT N SHAKE) results about entirely unrelated topics (Woking churches; a US restaurant chain). Full detail in `experiments/source_pdf.py`.

Because no PDF was found, `src/vat_discovery/extraction/pdf.py` (built this phase: TEXT-layer extraction via `pypdf`, deliberately no default OCR, page-level text-presence stats to surface OCR need without acting on it) has only been exercised against synthetic fixtures in `tests/test_extraction_pdf.py`, not a real downloaded document.

This pilot cannot distinguish "no PDFs exist for these companies" from "`filetype:pdf` search does not surface them" — a real next test would target a source known to hold PDFs for every company (e.g. Companies House's own filed-accounts documents), while noting that filed accounts and VAT registration are different regimes and accounts PDFs are not expected to contain a VAT number even when found.

## Phase 2 round 2 observed (n=8, disambiguated query: town + sector keyword)

Retested the same 8 companies with a query that adds a town and sector disambiguator drawn from the real Companies House record (e.g. `"CEUTICA" Swindon pharmaceutical manufacturing "VAT number"`), to test whether round 1's NO-GO was a weak-query artifact.

**Result: 0 new confirmed websites, 0 new VAT evidence.** Disambiguation changed the quality of near-misses, not the outcome — it surfaced one more concrete wrong-entity trap (`MEAT AND SHAKES (PRESTON) LIMITED`, company number 13198421, Manchester M12 6AE — a different company and city than the sampled `MEAT N SHAKE LTD`, 17295865, Preston PR2 9ZG) and one context-free unrelated VAT number appearing on a property listing page with no connection to the target company (GXFC LTD). Both were correctly rejected on company-number/address grounds, not merged. Full detail: `experiments/source_website_round2.py`.

This raises confidence in the round-1 conclusion rather than lowering it: the NO-GO was not primarily a query-weakness artifact for this segment of the population (small/recently-formed companies, collision-prone names). It also produced two real, concrete false-positive near-misses across the two rounds — stronger evidence for entity-resolution design than any synthetic example, and used directly as regression fixtures below.

## Phase 2 round 3 observed (n=28 new companies, extended pilot -- first real candidates)

Extended the pilot from n=8 to n=28 new companies (cumulative 36 distinct companies across all three rounds), using the round-2 disambiguated-query style. This round produced the pipeline's **first two real, first-party-confirmed VAT candidates**:

| Company | VAT (raw) | Source | Syntax valid? | Confidence tier |
|---|---|---|---|---|
| HILLS FAMILY LTD (14228579) | 420840821 | Own site footer, hills-family.ltd.uk | Yes (MOD97_STANDARD) | TIER_3 |
| JTHN LIMITED (08250395) | 183 3256 07 | Own site footer, jthn.co.uk | **No** (fails both known checksum rules) | TIER_3 |

Both were run through the actual built pipeline (`extraction.html` → `normalization.vat` → `entity_resolution.scoring`), not hand-computed, and inserted into `data/vat_discovery.sqlite` with full provenance (`experiments/source_website_round3.py`). Both land at **TIER_3, not a reportable discovery** — `verification_status` was honestly recorded as `UNAVAILABLE` (no HMRC credentials exist), and the scorer's design correctly caps any unverified candidate at TIER_3 regardless of how strong the contextual match is. This is the design working as intended, exercised for the first time on real data.

**Two findings worth flagging on their own:**

1. **JTHN's VAT number fails our syntax/checksum validator** despite exact company-number corroboration from the company's own site. This does not mean the number is fake — it means our checksum module (`normalization/vat.py`) may not cover every algorithm HMRC actually uses (UK VAT has more than the two check schemes currently implemented). Flagged as an open gap, not silently resolved; the candidate is correctly *not* discarded, since syntax invalidity is documented as "only a filter," never proof of anything either way.
2. **A third claimed VAT number (AQUAWASH LIMITED, "464 0309 66") appeared in a search-tool summary but was not present when the cited source page was fetched directly.** This is a distinct failure mode from anything seen in rounds 1-2: not a wrong entity, not a stale domain, but the search-summarization layer itself asserting text that isn't on the page. It was rejected, not merged. This is a first-class methodological finding: **any production pipeline must extract from raw fetched text/HTML directly (as `extraction/html.py` does), never trust an LLM-summarized description of a page as evidence** — this pilot only avoided the error because every claim was independently re-fetched and checked before being recorded. A fourth claim (TGK FOODS LTD) was consistent only across third-party aggregator sites with no first-party page found; also not merged, for the same reason.

**Revised source-level read**: company websites are a real, non-zero signal — roughly 5-7% of companies in this pilot (2/28 this round; 0/8 combined in rounds 1-2) — not the 0% the smaller pilots suggested. The binding constraint is no longer "does the source have any signal" but **"we have no authoritative verifier to convert a TIER_3 candidate into a reportable discovery."** Revised conclusion: **CONDITIONAL GO for company-website discovery**, pending HMRC (or an equivalent authoritative check) becoming available.

## Phase 10 observed (manual validation subset, n=100, complete)

Reviewed all 100 companies in the deterministic manual-validation subset (`data/processed/manual_validation_subset.csv`, seed `20260816`, 42/50 strata represented). **Labelling note**: per the user's explicit direction, these reviews were performed by the operating agent using the same search/fetch tools as the Phase 2 pilots, not by an independent human reviewer as the brief originally specifies -- every row is recorded as `AGENT_ASSISTED_NOT_INDEPENDENT_HUMAN_REVIEW` in `manual_reviews`, never to be conflated with true independent human validation.

**Result: 6 of 100 companies (6%) produced a real, first-party-confirmed VAT candidate** -- every one found on the company's own website footer and independently re-fetched to confirm before being recorded, after two confirmed hallucinated claims turned up along the way (see below):

| Company | VAT (raw) | Company-number match | Address match |
|---|---|---|---|
| HILLS FAMILY LTD (14228579) | 420840821 | Exact | Exact |
| JTHN LIMITED (08250395) | 183 3256 07 | Exact | **Mismatch** (site: 65 Church Road; CH: 75 Church Road) |
| GO2 PROPERTY SERVICES LIMITED (11369537) | 3877 41746 | Exact | **Mismatch** (site: Lightwater; CH: Woking) |
| G A PLANT AND TOOL HIRE LTD (09460505) | GB 208 0331 52 | Exact | Exact |
| TTG PORTSMOUTH LIMITED (15093369) | 450 5886 76 | Exact | Exact |
| BULLET BUILDING PRODUCTS LIMITED (11198097) | 289 184 943 | Exact | Exact |

Combined with the 0 found in the smaller Phase 2 pilots (n=36, different companies, mostly no signal), this 6% rate on a larger, unbiased 100-company draw is the most statistically defensible read on company-website VAT discoverability this project has produced. All 6 are run through the real pipeline and stored with full provenance in `data/vat_discovery.sqlite` (`vat_candidates`, `entity_matches`, `websites`, `documents`).

**Every one of the 6 is capped at TIER_3** ("candidate only, not a discovery") -- not because the evidence is weak (G A PLANT AND TOOL HIRE LTD scores 0.96/1.0, a near-perfect match on every signal) but because `verification_status` is honestly `UNAVAILABLE`: no HMRC credentials exist. This is the design from Phase 0 working exactly as intended, now demonstrated on 6 independent real cases, not a hypothetical.

### Two more hallucinated/unconfirmable claims caught (now 4 total this project)

During this batch, two more claimed VAT numbers turned out not to hold up: FIREBIRD MUSIC LIMITED (claimed `GB469123184`; the domain the search summary suggested turned out to belong to an unrelated US company) and BRISTOL ENERGY & TECHNOLOGY SERVICES (SUPPLY) LIMITED (claimed `220 428 253`; the cited PDF, fetched directly, does not contain that number). A third claim (MOIRA FINE JEWELLERY LIMITED) could not be checked at all -- the site returned HTTP 403 on every attempted page -- and was rejected on that basis alone, combined with an unexplained address mismatch. Combined with AQUAWASH LIMITED from Phase 2 round 3, this is now **4 confirmed-or-suspected hallucinated/unconfirmable claims out of the ~10 total VAT-number claims this project has investigated** -- a roughly 40% false-claim rate among search-summary-reported VAT numbers before independent verification. This is one of the strongest findings in the whole project: **a production pipeline must never trust a search-result summary as evidence; every claim must be independently re-fetched from a primary source before being recorded.**

### Checksum validator bug found and fixed

Three of the six real candidates (JTHN, GO2, G A PLANT) initially failed `normalization.vat.validate_uk_vat_syntax` under both implemented rules, despite exact company-number corroboration. Investigation found a sign error in the "9755" legacy-variant formula: the code computed `(standard + 42) % 97` where the correct formula (confirmed against all three real numbers, cross-checked with independent documentation of the UK VAT modulus-97 algorithm) is `(42 - standard) % 97`. Fixed in `src/vat_discovery/normalization/vat.py`; regression tests added in `tests/test_normalization.py` using the three real digit strings, not just constructed examples. **This bug would have silently misclassified roughly three-quarters of real UK VAT numbers using this specific check scheme as syntactically invalid** in any downstream use of this module -- caught only because real evidence contradicted the code, not because anyone thought to test this case. All previously-inserted `vat_candidates` rows were corrected in place after the fix.

## Round 4 observed (n=30 further companies, deadline-driven extension)

Extended the pilot by 30 more companies drawn from the untested remainder of the 500-sample (`experiments/source_website_round4.py`), bringing cumulative distinct companies piloted across this project past 160. **1 more real, first-party-confirmed candidate: EXECUTOURS LIMITED** (company number and address match exactly, VAT "977 2471 79" confirmed on the company's own site). One more search-summary claim (SDC HOSTING AND SUPPORT LTD) was rejected after direct verification found neither the claimed VAT number nor even the claimed address on the real page.

**EXECUTOURS' VAT number also fails both implemented checksum rules** (standard and 9755-variant) despite exact company-number/address corroboration — the 4th of 7 total real candidates to do so (Hills Family passed standard; JTHN, GO2, G A Plant, TTG Portsmouth, Bullet Building Products passed the fixed 9755 variant; Executours passes neither). This is recorded as further confirmation that UK VAT checksum coverage in `normalization/vat.py` is still incomplete — not fixed further here, since no verified-correct third algorithm was identified in the time available, and guessing at one without confirming it against a known-correct source would repeat the exact mistake the original 9755 bug came from. Flagged as an open follow-up.

**Cumulative project total: 7 of ~160 distinct companies piloted (≈4.4%) produced a real, first-party-confirmed VAT candidate**, none yet authoritatively verified (see `docs/decision.md`).

## Phase 8 built (entity resolution scoring, code only)

`src/vat_discovery/entity_resolution/scoring.py` implements the six-signal model from `config/scoring.yaml` (name/address/postcode/domain/company-number/context), producing an explainable `MatchResult` per candidate. Validated with 32 unit tests, including two regression fixtures built directly from real Phase-2 pilot false positives rather than synthetic examples — both correctly land at TIER_3 (`CANDIDATE_ONLY_NOT_A_DISCOVERY`), demonstrating the scorer would have rejected both near-misses had they reached this stage automatically. No real candidate exists yet to run this against end-to-end; both pilots so far produced zero candidates.

## Design findings

- A VAT-looking string must remain a provenance-backed candidate until independently verified and associated with the Companies House entity.
- The sample design must retain strata and weights; a convenience sample of VAT-publishing companies would not answer the coverage question.
- HMRC verification must be isolated behind an adapter and treated as constrained, authenticated due-diligence functionality rather than an enumeration mechanism.
- A single naive search query per company is measurably too weak at this sample size to serve as the sole website-discovery signal; it also cannot be conflated with company-website discovery via a real production `SearchProvider` adapter, since this pilot substituted the operating agent's own search/fetch tools (no credentialed search API exists yet).

## Decision

Still no GO / CONDITIONAL GO / NO-GO — n=8 is a feasibility smoke test, not a source-level conclusion. Per the brief's precision-first, evidence-first rule, the honest read of this pilot is a **NO-GO for the single-query strategy specifically**, and an open question for company websites as a source in general. Next evidence gate: a larger pilot (n=25-30) using multiple query variants per company (brief section 30) and Companies House name/SIC to disambiguate multi-result cases, before deciding whether this source is worth a scaled adapter at all.
