# Source matrix

| Source | What it contributes | Evidence so far | Decision |
|---|---|---|---|
| Companies House bulk data | Company identity, status, SIC, and address | 2026-08-01 snapshot ingested: 5.19M active companies and a 500-company stratified sample. | Use as the population backbone. Reconfirm reuse terms before commercial use. |
| Company websites | VAT text in legal, footer, or contact content | 7 first-party candidates from roughly 160 companies. All remain TIER_3 until verification. | Continue as a discovery source, with direct fetches, caching, throttling, and terms checks. |
| Open-web search | Website and document leads | Useful for leads, but search summaries produced several claims that failed source checks. | Use a real `SearchProvider` that returns raw results; never treat summaries as evidence. |
| HMRC Check a UK VAT Number API | Authoritative verification | Adapter works in Sandbox; production access has not been requested. | Required before producing final VAT records. |
| Open-web PDFs | Possible VAT text in terms, invoices, or documents | `filetype:pdf` pilot found no company-specific documents in 8 cases. | Do not use as a standalone source. Test a targeted document source before ruling PDFs out completely. |
| Procurement or spend records | Supplier identifiers and supporting evidence | Not tested. | Assess licence, freshness, and coverage before use. |
| Business directories | Possible website leads | Not tested as a primary source. | Secondary corroboration only; not enough for a final decision by itself. |

The results above describe the POC, not population-wide coverage or commercial
performance. Details and experiment links are in [findings.md](findings.md).
