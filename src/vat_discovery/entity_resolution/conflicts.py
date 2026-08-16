"""Conflict detection (brief section 18): if multiple sources produce
different VAT numbers for the same company, this must never be resolved
silently by picking one. It becomes an OPEN conflict record, and an open
conflict blocks that company from producing a final TIER_1 result --
precision-first, even when one of the disagreeing candidates individually
scores high enough to qualify.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateForConflictCheck:
    candidate_id: int
    company_id: int
    normalized_vat: str | None


@dataclass(frozen=True)
class ConflictRecord:
    company_id: int
    candidate_ids: tuple[int, ...]
    conflict_type: str
    status: str


def detect_conflicts(candidates: list[CandidateForConflictCheck]) -> list[ConflictRecord]:
    """Groups candidates by company; a company with more than one distinct
    normalized VAT value across its candidates is an open conflict.
    Candidates with no normalized value (failed normalization) are excluded
    from comparison -- they are a different failure mode (CANDIDATE_FAILED_SYNTAX),
    not a disagreement between two otherwise-plausible values."""
    by_company: dict[int, list[CandidateForConflictCheck]] = defaultdict(list)
    for candidate in candidates:
        if candidate.normalized_vat is not None:
            by_company[candidate.company_id].append(candidate)

    conflicts = []
    for company_id, group in by_company.items():
        distinct_values = {candidate.normalized_vat for candidate in group}
        if len(distinct_values) > 1:
            conflicts.append(ConflictRecord(
                company_id=company_id,
                candidate_ids=tuple(sorted(candidate.candidate_id for candidate in group)),
                conflict_type="DISAGREEING_VAT_CANDIDATES",
                status="OPEN",
            ))
    return conflicts


def companies_with_open_conflicts(conflicts: list[ConflictRecord]) -> frozenset[int]:
    return frozenset(conflict.company_id for conflict in conflicts if conflict.status == "OPEN")


def gate_high_confidence_results(company_ids_at_tier_1: list[int], conflicts: list[ConflictRecord]) -> tuple[list[int], list[int]]:
    """Splits TIER_1 company IDs into (clear, blocked-by-open-conflict).
    A company can score TIER_1 on one candidate and still be blocked here if
    a different candidate for the same company disagrees -- scoring and
    conflict-gating are deliberately separate steps."""
    blocked = companies_with_open_conflicts(conflicts)
    clear = [company_id for company_id in company_ids_at_tier_1 if company_id not in blocked]
    held = [company_id for company_id in company_ids_at_tier_1 if company_id in blocked]
    return clear, held
