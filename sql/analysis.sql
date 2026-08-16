-- Review queue: verified candidates that did not become an accepted Tier 1 match.
SELECT c.candidate_id, c.company_id, c.normalized_vat, c.source_url, v.registered_name,
       m.total_score, m.confidence_tier, m.decision, m.explanation
FROM vat_candidates c
JOIN vat_verifications v ON v.candidate_id = c.candidate_id AND v.status = 'VERIFIED'
LEFT JOIN entity_matches m ON m.candidate_id = c.candidate_id
WHERE m.match_id IS NULL OR m.confidence_tier <> 'TIER_1' OR m.decision <> 'ACCEPT'
ORDER BY c.company_id, c.candidate_id;

-- Open conflicts must never be emitted as high-confidence final records.
SELECT conflict_id, company_id, candidate_ids, conflict_type, status, created_at
FROM conflicts
WHERE status IN ('OPEN', 'MANUAL_REVIEW')
ORDER BY created_at;
