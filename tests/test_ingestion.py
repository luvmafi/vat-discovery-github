import csv
from pathlib import Path

from vat_discovery.ingestion.companies_house import convert, convert_row, parse_incorporation_date, parse_sic_codes

FIXTURE = Path(__file__).parent / "fixtures" / "companies_house_sample.csv"


def test_parse_sic_codes_extracts_leading_numeric_code_and_skips_none_supplied():
    row = {"SICCode.SicText_1": "41200 - Construction of buildings", "SICCode.SicText_2": "None Supplied"}
    assert parse_sic_codes(row) == ["41200"]


def test_parse_incorporation_date_converts_dd_mm_yyyy_to_iso():
    assert parse_incorporation_date("15/03/2018") == "2018-03-15"
    assert parse_incorporation_date("") == ""
    assert parse_incorporation_date("not-a-date") == ""


def test_convert_row_drops_rows_missing_number_or_name():
    assert convert_row({"CompanyNumber": "SC1", "CompanyName": ""}) is None
    assert convert_row({"CompanyNumber": "", "CompanyName": "X LTD"}) is None


def test_convert_row_joins_address_and_maps_fields():
    with FIXTURE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    converted = convert_row(rows[0])
    assert converted["companies_house_number"] == "SC000001"
    assert converted["raw_company_name"] == "EXAMPLE FIXTURE BUILDERS LTD"
    assert converted["sic_codes"] == "41200"
    assert converted["incorporation_date"] == "2018-03-15"
    assert converted["postcode"] == "TE1 1ST"
    assert "1 Test Street" in converted["raw_address"] and "Testville" in converted["raw_address"]


def test_convert_streams_and_filters_by_status_and_reports_stats(tmp_path):
    output_csv = tmp_path / "population.csv"
    stats = convert([FIXTURE], output_csv, status_filter="Active")
    assert stats["rows_read"] == 4
    assert stats["rows_dropped_missing_fields"] == 1
    assert stats["rows_kept"] == 2
    with output_csv.open(newline="", encoding="utf-8") as handle:
        kept = list(csv.DictReader(handle))
    assert {row["companies_house_number"] for row in kept} == {"SC000001", "SC000002"}


def test_convert_with_no_status_filter_keeps_dissolved_too(tmp_path):
    output_csv = tmp_path / "population.csv"
    stats = convert([FIXTURE], output_csv, status_filter=None)
    assert stats["rows_kept"] == 3


def test_convert_tolerates_leading_space_padded_header(tmp_path):
    padded = tmp_path / "padded.csv"
    padded.write_text(
        'CompanyName, CompanyNumber,CompanyStatus, RegAddress.AddressLine1,RegAddress.PostCode,IncorporationDate\n'
        '"PADDED HEADER FIXTURE LTD","SC000005","Active","1 Padding Way","PD1 1PD","01/01/2020"\n',
        encoding="utf-8",
    )
    output_csv = tmp_path / "population.csv"
    stats = convert([padded], output_csv, status_filter="Active")
    assert stats["rows_kept"] == 1
    with output_csv.open(newline="", encoding="utf-8") as handle:
        kept = list(csv.DictReader(handle))
    assert kept[0]["companies_house_number"] == "SC000005"
