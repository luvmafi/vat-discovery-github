# Economics

The model estimates the cost of discovery, extraction, storage, review, and
verification at several scales. It separates measured ratios, dated prices, and
assumptions. A cost per verified VAT is not available yet because no candidate
has been verified against production HMRC data.

## Inputs

| Input | Value | Basis |
|---|---:|---|
| Search requests per company | 1.214 | Observed in the 28-company website pilot. |
| Search price | $15.00 / 1,000 queries | SerpAPI Developer tier, checked 2026-08-16. |
| OCR pages per company | 0.0 | Observed; OCR was not used in the POC. |
| OCR price | $1.50 / 1,000 pages | Google Cloud Vision, checked 2026-08-16. |
| Storage per company record | 5 KB | Estimate; not measured at scale. |
| Storage price | $0.023 / GB-month | AWS S3 Standard, checked 2026-08-16. |
| Manual review | 3 minutes per company | Planning assumption, not a timed human measurement. |
| Review labour | £14.00/hour | Market estimate, checked 2026-08-16. |
| HMRC lookup | $0.00 per call | Documented as free once credentialed; access unavailable. |
| Engineering and operations | — | Not estimated. |

The full input metadata is in `config/economics.yaml`; the calculation is in
`src/vat_discovery/economics/model.py`.

## Modelled cost

| Companies | Total cost | Cost/company | Expected candidates* | Cost/candidate | Cost/verified VAT |
|---:|---:|---:|---:|---:|---|
| 1,000 | $963.21 | $0.9632 | 55.6 | $17.32 | Unavailable |
| 10,000 | $9,632.10 | $0.9632 | 556.0 | $17.32 | Unavailable |
| 40,000 | $38,528.40 | $0.9632 | 2,224.0 | $17.32 | Unavailable |
| 1,000,000 | $963,210.11 | $0.9632 | 55,600.0 | $17.32 | Unavailable |

*Uses the 5.56% candidate rate from the earlier 36-company website pilot.
The 4–6% range in [findings.md](findings.md) is a more useful summary of the
current uncertainty.

These are linear estimates, not production measurements. They exclude the
engineering and operational cost of running a real discovery service, and they
do not assume bulk discounts. Production credentials would make the missing
`cost/verified VAT` metric measurable; a timed independent review and a real
search-provider run would replace the two largest operating assumptions.
