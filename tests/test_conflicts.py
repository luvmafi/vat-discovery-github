from vat_discovery.entity_resolution.conflicts import (
    CandidateForConflictCheck,
    detect_conflicts,
    gate_high_confidence_results,
)


def test_no_conflict_when_all_candidates_for_a_company_agree():
    candidates = [
        CandidateForConflictCheck(1, company_id=100, normalized_vat="123456789"),
        CandidateForConflictCheck(2, company_id=100, normalized_vat="123456789"),
    ]
    assert detect_conflicts(candidates) == []


def test_conflict_when_two_candidates_disagree():
    candidates = [
        CandidateForConflictCheck(1, company_id=100, normalized_vat="123456789"),
        CandidateForConflictCheck(2, company_id=100, normalized_vat="987654321"),
    ]
    conflicts = detect_conflicts(candidates)
    assert len(conflicts) == 1
    assert conflicts[0].company_id == 100
    assert conflicts[0].candidate_ids == (1, 2)
    assert conflicts[0].status == "OPEN"


def test_candidates_with_failed_normalization_are_not_compared():
    candidates = [
        CandidateForConflictCheck(1, company_id=100, normalized_vat=None),
        CandidateForConflictCheck(2, company_id=100, normalized_vat="123456789"),
    ]
    assert detect_conflicts(candidates) == []


def test_different_companies_never_conflict_with_each_other():
    candidates = [
        CandidateForConflictCheck(1, company_id=100, normalized_vat="123456789"),
        CandidateForConflictCheck(2, company_id=200, normalized_vat="987654321"),
    ]
    assert detect_conflicts(candidates) == []


def test_gate_blocks_tier_1_company_with_open_conflict():
    candidates = [
        CandidateForConflictCheck(1, company_id=100, normalized_vat="123456789"),
        CandidateForConflictCheck(2, company_id=100, normalized_vat="987654321"),
    ]
    conflicts = detect_conflicts(candidates)
    clear, held = gate_high_confidence_results([100, 200], conflicts)
    assert clear == [200]
    assert held == [100]
