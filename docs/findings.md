# Findings

## Executive summary

The project tested whether a UK company's VAT number can be found responsibly
from public web evidence. The answer is: sometimes, but web evidence alone is
not enough to create a final record.

- A dated Companies House snapshot supplied 5,190,464 active companies.
- The project created a reproducible, stratified sample of 500 companies and a
  100-company validation subset.
- Seven of roughly 160 companies tested produced a VAT candidate supported by a
  first-party website. This is a discovery rate of about 4.4%; the 100-company
  subset produced 6 candidates (6%).
- No candidate has been authoritatively verified because HMRC production access
  has not been requested. All candidates remain TIER_3.
- Search-result summaries created several false leads: about 4 of roughly 10
  VAT claims investigated did not appear in the primary source when fetched.

The practical conclusion is `CONDITIONAL GO`: company websites are worth using
as a discovery source, provided every claim is fetched, recorded, and then
verified by an authoritative service.

## Candidate results

All entries below were found on the company's own website and re-fetched before
they were recorded. They are candidates, not verified VAT records.

| Company | Company-number match | Address match | Current tier |
|---|---|---|---|
| Hills Family Ltd | Exact | Exact | TIER_3 |
| JTHN Limited | Exact | Different website address | TIER_3 |
| GO2 Property Services Limited | Exact | Different website address | TIER_3 |
| G A Plant and Tool Hire Ltd | Exact | Exact | TIER_3 |
| TTG Portsmouth Limited | Exact | Exact | TIER_3 |
| Bullet Building Products Limited | Exact | Exact | TIER_3 |
| Executours Limited | Exact | Exact | TIER_3 |

The full evidence, raw values, source documents, and scores are in
`data/vat_discovery.sqlite` and the corresponding experiment scripts.

## What each pilot showed

| Work | Sample | Result | Takeaway |
|---|---:|---|---|
| Initial website search | 8 companies | 0 candidates | One generic query was too weak for small or collision-prone companies. |
| Disambiguated website retest | Same 8 | 0 new candidates | Better queries improved context, but did not turn this segment into a useful source. |
| Extended website pilot | 28 new companies | 2 candidates | First-party website evidence exists and can be captured by the pipeline. |
| Validation subset | 100 companies | 6 candidates | Best single estimate of the website signal so far: 6%, with the review caveat below. |
| Round 4 extension | 30 further companies | 1 candidate | Cumulative result reached 7 candidates across roughly 160 companies. |
| Open-web PDF search | 8 companies | 0 company-specific PDFs | `filetype:pdf` search alone is not a useful source on this evidence. |

The 100-company reviews were agent-assisted and are labelled as such in the
database. They are useful operational evidence, but do not replace the
independent human review requested in the original brief.

## Failure modes that mattered

### Name collisions and weak context

The pilot rejected an unrelated South African retailer for KNOTAGAIN
INTERNATIONAL LTD and a different company, MEAT AND SHAKES (PRESTON) LIMITED,
when looking for MEAT N SHAKE LTD. These are why a name match alone is never
enough; the final rule requires stronger corroboration such as a company number
or postcode.

### Search summaries are leads, not evidence

AQUAWASH, FIREBIRD MUSIC, BRISTOL ENERGY & TECHNOLOGY SERVICES, and SDC HOSTING
AND SUPPORT all produced claims that did not survive a direct check of the
suggested source. Production discovery must extract from fetched page content,
not from an LLM or search-summary description of the page.

### Website and registered-office addresses can differ

JTHN and GO2 had exact company-number evidence but a different address on their
websites. Treating any address difference as a rejection would lose genuine
candidates. The scoring rule therefore accepts a company-number match as the
stronger signal.

### Checksum coverage is incomplete

Real candidates exposed a sign error in the 9755 checksum variant. The fix is
covered by regression tests. Executours still fails the implemented checksum
rules despite strong first-party evidence, so checksum validation remains a
diagnostic feature rather than a gate.

## What remains before a final result

`HmrcVatVerifier` has been tested against the HMRC Sandbox, but the Sandbox
returns only test data. The next step is to request production credentials and
verify the seven existing candidates. Until then, no VAT number in this project
should be reported as a confirmed discovery.

## Supporting material

- `experiments/source_website.py`, `source_website_round2.py`,
  `source_website_round3.py`, and `source_website_round4.py` record the web
  discovery rounds.
- `experiments/source_pdf.py` records the PDF pilot.
- `experiments/manual_validation_review.py` records the validation subset.
- `src/vat_discovery/entity_resolution/scoring.py` contains the scoring logic.
