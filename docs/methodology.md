# Methodology

## Scope

The population backbone will be a documented, dated Companies House extract restricted to active UK companies. VAT is not expected in that extract. The unit of analysis is the Companies House number; VAT identifiers are separate, evidence-derived candidates.

## Population acquisition

Companies House publishes a free monthly bulk snapshot ("Basic Company Data") of live company records as CSV, distributed as one ~470MB file or seven smaller parts, at https://download.companieshouse.gov.uk/en_output.html. It is explicitly unsupported and updated within 5 working days of month end. Companies House has stated the product carries no reuse restriction as statutory public information, though this is not a written Open Government Licence grant and should be re-confirmed before commercial use.

This snapshot is downloaded manually — it is a large, monthly-changing file and downloading it is a deliberate human action to record, not something the pipeline does silently. `src/vat_discovery/ingestion/companies_house.py` then streams the local CSV part(s), maps the relevant columns (`CompanyNumber`, `CompanyName`, `CompanyStatus`, `RegAddress.*`, `IncorporationDate`, `SICCode.SicText_1..4`) onto the sampler's population schema, filters by `CompanyStatus` (default `Active`), and writes a manifest (source URL, claimed snapshot date, row counts read/kept/dropped, status distribution, generated-at timestamp) alongside the output CSV. The manifest is the record required before Phase 1 sampling proceeds.

## Sampling

Combined industry/age strata use the SIC mapping in `config/industry_mapping.yaml` and age bands 0–2, 3–5, 6–10, 11–20, and 21+ years. Allocation is proportional using largest remainder. The export query/version, as-of date, exclusions, counts, seed, and generated manifest must be recorded. A zero allocation in a small proportional stratum is a known design outcome, not silently corrected.

## Pipeline contracts

1. Discovery may produce multiple website/domain candidates, each with evidence and confidence.
2. Extraction creates an immutable candidate with raw match, context, URL, document hash, and parser version.
3. Normalization creates a comparison value without overwriting raw evidence; checksum validation is only a feature.
4. An authoritative verifier returns a structured result, separate from entity matching.
5. Entity resolution records explainable scores, contradictions, and a tier. Tier 1 requires verified status plus name and postcode or explicit company-number evidence; thresholds are configuration, not claims of truth.
6. Conflicts and ambiguity never emit a final high-confidence identifier.

## Experiment record

Each source test writes a `source_experiments` row containing hypothesis, population/sample, configuration/code version, observations, failures, conclusion, and next action. Report observed coverage, never recall, unless an independently grounded truth set exists.
