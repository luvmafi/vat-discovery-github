from pathlib import Path

from vat_discovery.sampling.manual_validation_subset import select

SAMPLE_CSV = Path("data/processed/sample.csv")


def test_select_returns_target_size_unique_companies():
    selected, manifest = select(SAMPLE_CSV, target_size=20, seed=1)
    assert len(selected) == 20
    assert len({row["companies_house_number"] for row in selected}) == 20
    assert manifest["subset_size"] == 20


def test_select_is_deterministic_for_same_seed():
    first, _ = select(SAMPLE_CSV, target_size=20, seed=1)
    second, _ = select(SAMPLE_CSV, target_size=20, seed=1)
    assert [row["companies_house_number"] for row in first] == [row["companies_house_number"] for row in second]


def test_different_seeds_can_select_different_companies():
    first, _ = select(SAMPLE_CSV, target_size=20, seed=1)
    second, _ = select(SAMPLE_CSV, target_size=20, seed=2)
    first_numbers = {row["companies_house_number"] for row in first}
    second_numbers = {row["companies_house_number"] for row in second}
    assert first_numbers != second_numbers
