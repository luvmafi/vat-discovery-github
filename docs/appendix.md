# Appendix

The database at `data/vat_discovery.sqlite` contains the reproducible outputs
from the POC:

- `source_experiments` records each pilot's hypothesis, sample, configuration,
  observations, failures, conclusion, and next action.
- `vat_candidates` and `entity_matches` contain the seven first-party website
  candidates, their raw evidence, checksum result, and match explanation.
- `manual_reviews` contains the 100 validation-subset reviews, labelled
  `AGENT_ASSISTED_NOT_INDEPENDENT_HUMAN_REVIEW`.
- `websites` and `documents` preserve fetched-source provenance, including
  pages that did not yield a candidate.

Relevant source data includes `data/processed/sample.csv`,
`data/processed/manual_validation_subset.csv`, the Companies House snapshot
manifest, and the sampling manifests. The experiment scripts are under
`experiments/`; [findings.md](findings.md) provides the short narrative.

`experiments/hmrc_experiment.py` remains a dry-run-only scaffold. It does not
create VAT candidates or make network requests.
