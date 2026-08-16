from collections import Counter
from datetime import date

from vat_discovery.sampling.stratify import age_bucket, proportional_allocation


def test_age_buckets_and_proportional_total():
    assert age_bucket(date(2024, 8, 15), date(2026, 8, 15)) == "0_2"
    allocation = proportional_allocation(Counter({"A": 7, "B": 3}), 5)
    assert sum(allocation.values()) == 5
    assert allocation == {"A": 4, "B": 1}


def test_target_cannot_exceed_population():
    try:
        proportional_allocation(Counter({"A": 1}), 2)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
