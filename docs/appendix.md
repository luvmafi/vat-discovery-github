# Appendix — experiment outputs

`experiments/hmrc_experiment.py` remains a local dry-run-only scaffold: it creates no VAT candidates and makes no network requests (Phase 0 design, unchanged).

Real experiment output now exists and is queryable directly from `data/vat_discovery.sqlite`:

- `source_experiments` — one row per pilot round (`experiments/source_website.py`, `_round2.py`, `_round3.py`, `source_pdf.py`), each with hypothesis, sample description, observed results (JSON), failure modes, conclusion, and next action.
- `vat_candidates` / `entity_matches` — the 6 real, first-party-confirmed VAT candidates found across Phase 2 and Phase 10, each with raw evidence, syntax/checksum result, and a full explainable entity-resolution score.
- `manual_reviews` — all 100 rows from the Phase 10 manual-validation subset review (`experiments/manual_validation_review.py`), each tagged `reviewer = AGENT_ASSISTED_NOT_INDEPENDENT_HUMAN_REVIEW`.
- `websites`, `documents` — provenance for every fetched source, including the ones that produced no evidence.

Source data files: `data/processed/sample.csv` (500-company sample), `data/processed/manual_validation_subset.csv` (100-company subset), `data/raw/companies_house_snapshot_manifest.json` and `data/processed/*_manifest.json` (acquisition/sampling manifests), `data/intermediate/manual_review_batch_0{1..5}.json` (raw review batch inputs).

See `docs/findings.md` for the narrative summary and `research_report.md` for the phase-by-phase investigation log.
