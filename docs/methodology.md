# Methodology

## Scope

The population is active UK companies from a dated Companies House bulk
snapshot. Companies House does not publish VAT numbers in that extract, so VAT
values are treated as separately sourced candidates. The Companies House number
is the stable unit used to join evidence and decisions.

## Population and sample

The snapshot is downloaded manually and recorded with its source URL, stated
date, input counts, output counts, and status distribution. The ingestion code
streams the local CSV, maps the required identity and address fields, filters to
active companies, and writes a manifest alongside the processed data.

The sampler groups companies by SIC-derived industry and incorporation age.
It allocates the sample proportionally with the largest-remainder method, then
makes deterministic selections from a recorded seed. The manifest records the
snapshot, date, exclusions, stratum counts, seed, and sample weights.

## Evidence pipeline

1. Discovery produces one or more possible source pages for a company.
2. Extraction stores the raw VAT-like text, surrounding context, URL, document
   hash, and parser version.
3. Normalisation makes a comparison value without replacing the raw evidence.
   Checksum results are signals, not proof.
4. An authoritative verifier returns a separate structured result.
5. Entity resolution scores the name, address, postcode, domain, company
   number, and context. TIER_1 requires verified status plus strong entity
   corroboration.
6. Conflicting or ambiguous evidence stays out of the final dataset.

Each source experiment records the hypothesis, sample, configuration, observed
results, failures, conclusion, and next action. The project reports observed
coverage only; it does not claim recall without a grounded reference set.
