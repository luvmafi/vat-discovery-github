from pathlib import Path

import yaml

from vat_discovery.economics.model import compute_cost_breakdown

CONFIG = yaml.safe_load(Path("config/economics.yaml").read_text(encoding="utf-8"))


def test_rejects_non_positive_company_count():
    try:
        compute_cost_breakdown(0, CONFIG)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_cost_scales_linearly_with_company_count():
    small = compute_cost_breakdown(1000, CONFIG)
    large = compute_cost_breakdown(10000, CONFIG)
    assert abs(large.total_cost_usd - small.total_cost_usd * 10) < 1e-6
    assert abs(large.cost_per_company_usd - small.cost_per_company_usd) < 1e-9


def test_search_cost_uses_observed_ratio_and_market_price():
    result = compute_cost_breakdown(1000, CONFIG)
    expected = 1.214 * 1000 * 15.0 / 1000
    assert abs(result.search_cost_usd - expected) < 1e-6


def test_ocr_cost_is_zero_because_it_has_never_been_triggered():
    result = compute_cost_breakdown(1000, CONFIG)
    assert result.ocr_cost_usd == 0.0


def test_verified_discovery_rate_unavailable_yields_none_not_zero():
    result = compute_cost_breakdown(1000, CONFIG)
    assert result.cost_per_verified_vat_usd is None
    assert any("verified_discovery_rate" in item for item in result.unavailable_inputs)


def test_candidate_rate_is_available_and_positive():
    result = compute_cost_breakdown(1000, CONFIG)
    assert result.candidates_expected == 1000 * 0.0556
    assert result.cost_per_candidate_usd is not None
    assert result.cost_per_candidate_usd > result.cost_per_company_usd


def test_unavailable_inputs_flag_engineering_ops_and_verification():
    result = compute_cost_breakdown(1000, CONFIG)
    reasons = " ".join(result.unavailable_inputs)
    assert "engineering_ops" in reasons
    assert "verification" in reasons or "HMRC" in reasons


def test_four_reference_scales_all_compute_without_error():
    for count in (1_000, 10_000, 40_000, 1_000_000):
        result = compute_cost_breakdown(count, CONFIG)
        assert result.total_cost_usd > 0
        assert result.company_count == count
