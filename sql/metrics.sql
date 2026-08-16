-- Observed funnel metrics only. These are not population recall estimates.
SELECT
  (SELECT COUNT(*) FROM sample) AS companies_sampled,
  (SELECT COUNT(DISTINCT company_id) FROM websites WHERE status IN ('CONFIRMED','PROBABLE')) AS companies_with_candidate_websites,
  (SELECT COUNT(*) FROM vat_candidates) AS vat_candidates_found,
  (SELECT COUNT(*) FROM vat_verifications WHERE status = 'VERIFIED') AS verified_candidates,
  (SELECT COUNT(*) FROM entity_matches WHERE confidence_tier = 'TIER_1' AND decision = 'ACCEPT') AS high_confidence_matches;

-- Preserve both dangerous false-positive categories independently.
SELECT
  SUM(CASE WHEN v.status <> 'VERIFIED' THEN 1 ELSE 0 END) AS candidate_level_false_positives,
  SUM(CASE WHEN v.status = 'VERIFIED' AND m.decision = 'REJECT_WRONG_ENTITY' THEN 1 ELSE 0 END) AS entity_resolution_false_positives
FROM vat_candidates c
LEFT JOIN vat_verifications v ON v.candidate_id = c.candidate_id
LEFT JOIN entity_matches m ON m.candidate_id = c.candidate_id;
