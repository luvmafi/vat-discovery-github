"""Unit economics: cost per company processed and cost per high-confidence
verified VAT, at a given scale. Every input traces back to config/economics.yaml
with an explicit `basis` (OBSERVED_RATIO_TIMES_MARKET_PRICE / ESTIMATED /
ASSUMPTION_NOT_OBSERVED / HYPOTHETICAL_UNUSED_SO_FAR / UNAVAILABLE_UNTIL_CREDENTIALED
/ NOT_ESTIMATED). Nothing here invents a number without labelling where it
came from; a missing input produces `None` (UNAVAILABLE), never a silent 0.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostBreakdown:
    company_count: int
    search_cost_usd: float
    ocr_cost_usd: float
    storage_cost_usd: float
    manual_review_cost_usd: float
    verification_cost_usd: float
    total_cost_usd: float
    candidates_expected: float
    cost_per_company_usd: float
    cost_per_candidate_usd: float | None
    cost_per_verified_vat_usd: float | None
    unavailable_inputs: tuple[str, ...]


def compute_cost_breakdown(company_count: int, config: dict) -> CostBreakdown:
    if company_count <= 0:
        raise ValueError("company_count must be positive")

    inputs = config["inputs"]
    unavailable: list[str] = []

    search = inputs["search"]
    search_cost = search["observed_requests_per_company"] * company_count * search["price_per_1000_queries_usd"] / 1000

    ocr = inputs["ocr"]
    ocr_cost = ocr["observed_pages_per_company"] * company_count * ocr["price_per_1000_pages_usd"] / 1000

    storage = inputs["storage"]
    storage_gb = storage["estimated_kb_per_company_record"] * company_count / (1024 * 1024)
    storage_cost = storage_gb * storage["price_per_gb_month_usd"]

    manual = inputs["manual_review"]
    manual_minutes = manual["assumed_minutes_per_company"] * company_count
    manual_cost_usd = (manual_minutes / 60) * manual["hourly_rate_gbp"] * config["fx_gbp_to_usd"]

    verification = inputs["verification"]
    if verification["basis"] == "UNAVAILABLE_UNTIL_CREDENTIALED":
        unavailable.append("verification (no HMRC credentials)")
    verification_cost = verification["price_per_call_usd"] * company_count

    if inputs["engineering_ops"]["basis"] == "NOT_ESTIMATED":
        unavailable.append("engineering_ops (no defensible unit figure)")

    total_cost = search_cost + ocr_cost + storage_cost + manual_cost_usd + verification_cost
    cost_per_company = total_cost / company_count

    rates = config["observed_pipeline_rates"]
    candidates_expected = company_count * rates["candidate_discovery_rate"]
    cost_per_candidate = total_cost / candidates_expected if candidates_expected > 0 else None

    verified_rate = rates.get("verified_discovery_rate")
    if verified_rate is None:
        unavailable.append("verified_discovery_rate (no candidate has ever been authoritatively verified)")
        cost_per_verified_vat = None
    else:
        verified_expected = company_count * verified_rate
        cost_per_verified_vat = total_cost / verified_expected if verified_expected > 0 else None

    return CostBreakdown(
        company_count=company_count,
        search_cost_usd=search_cost,
        ocr_cost_usd=ocr_cost,
        storage_cost_usd=storage_cost,
        manual_review_cost_usd=manual_cost_usd,
        verification_cost_usd=verification_cost,
        total_cost_usd=total_cost,
        candidates_expected=candidates_expected,
        cost_per_company_usd=cost_per_company,
        cost_per_candidate_usd=cost_per_candidate,
        cost_per_verified_vat_usd=cost_per_verified_vat,
        unavailable_inputs=tuple(unavailable),
    )
