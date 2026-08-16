PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
  company_id INTEGER PRIMARY KEY, companies_house_number TEXT NOT NULL UNIQUE,
  raw_company_name TEXT NOT NULL, normalized_company_name TEXT NOT NULL,
  company_status TEXT NOT NULL, company_type TEXT, raw_address TEXT, normalized_address TEXT,
  postcode TEXT, sic_codes TEXT NOT NULL, industry_category TEXT NOT NULL,
  incorporation_date TEXT, company_age_years REAL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sample (
  company_id INTEGER PRIMARY KEY REFERENCES companies(company_id), stratum TEXT NOT NULL, sampled_at TEXT NOT NULL,
  sample_seed INTEGER NOT NULL, population_count_in_stratum INTEGER NOT NULL, sample_count_in_stratum INTEGER NOT NULL,
  sample_weight REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS websites (
  website_id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(company_id), domain TEXT NOT NULL,
  url TEXT NOT NULL, discovery_method TEXT NOT NULL, evidence_url TEXT, confidence REAL,
  status TEXT NOT NULL CHECK(status IN ('CONFIRMED','PROBABLE','AMBIGUOUS','REJECTED')), discovered_at TEXT NOT NULL,
  UNIQUE(company_id, url)
);
CREATE TABLE IF NOT EXISTS documents (
  document_id INTEGER PRIMARY KEY, company_id INTEGER REFERENCES companies(company_id), url TEXT NOT NULL UNIQUE,
  document_type TEXT NOT NULL, content_hash TEXT NOT NULL, discovered_at TEXT NOT NULL, retrieved_at TEXT,
  parser_version TEXT, retrieval_status TEXT
);
CREATE TABLE IF NOT EXISTS vat_candidates (
  candidate_id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(company_id), raw_vat TEXT NOT NULL,
  normalized_vat TEXT, syntax_valid INTEGER, syntax_rule TEXT, source_type TEXT NOT NULL, source_url TEXT NOT NULL,
  document_id INTEGER REFERENCES documents(document_id), extraction_method TEXT NOT NULL, matched_text TEXT NOT NULL,
  context TEXT NOT NULL, discovered_at TEXT NOT NULL, source_document_hash TEXT, parser_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vat_verifications (
  verification_id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES vat_candidates(candidate_id), vat_number TEXT NOT NULL,
  status TEXT NOT NULL, registered_name TEXT, registered_address TEXT, effective_date TEXT, verified_at TEXT NOT NULL,
  verifier TEXT NOT NULL, raw_response_reference TEXT, UNIQUE(candidate_id, verifier, verified_at)
);
CREATE TABLE IF NOT EXISTS entity_matches (
  match_id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES vat_candidates(candidate_id), company_id INTEGER NOT NULL REFERENCES companies(company_id),
  name_score REAL NOT NULL, address_score REAL NOT NULL, postcode_match INTEGER NOT NULL, domain_score REAL NOT NULL,
  company_number_match INTEGER NOT NULL, context_score REAL NOT NULL, total_score REAL NOT NULL,
  confidence_tier TEXT NOT NULL CHECK(confidence_tier IN ('TIER_1','TIER_2','TIER_3')),
  decision TEXT NOT NULL, explanation TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS conflicts (
  conflict_id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(company_id), candidate_ids TEXT NOT NULL,
  conflict_type TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('OPEN','RESOLVED','REJECTED','MANUAL_REVIEW')),
  resolution TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS manual_reviews (
  review_id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(company_id), candidate_id INTEGER REFERENCES vat_candidates(candidate_id),
  reviewer TEXT NOT NULL, reviewed_at TEXT NOT NULL, public_vat_evidence_found INTEGER, manually_identified_vat TEXT,
  evidence_url TEXT, evidence_type TEXT, confidence TEXT, decision TEXT, notes TEXT
);
CREATE TABLE IF NOT EXISTS source_experiments (
  experiment_id INTEGER PRIMARY KEY, source_name TEXT NOT NULL, source_type TEXT NOT NULL, hypothesis TEXT NOT NULL,
  population_description TEXT NOT NULL, sample_description TEXT NOT NULL, configuration_version TEXT NOT NULL,
  code_version TEXT NOT NULL, started_at TEXT NOT NULL, completed_at TEXT, observed_result_json TEXT,
  failure_modes TEXT, conclusion TEXT, next_action TEXT
);
CREATE INDEX IF NOT EXISTS idx_candidates_company ON vat_candidates(company_id);
CREATE INDEX IF NOT EXISTS idx_candidates_normalized_vat ON vat_candidates(normalized_vat);
CREATE INDEX IF NOT EXISTS idx_verifications_vat ON vat_verifications(vat_number);
