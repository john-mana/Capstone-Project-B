from pathlib import Path
import csv
import os
import tempfile
import search_flora


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def test_search_flora_database_basic(tmp_path, monkeypatch):
    # Prepare a temporary CSV file structured like Database/new_flora.csv
    header = [
        "Occurrence ID",
        "Scientific Name",
        "Event Date",
        "Dataset Name",
    ]
    rows = [
        ["1", "Acacia longifolia", "2020-05-01", "DatasetA"],
        ["2", "Eucalyptus globulus", "2021-03-15", "DatasetB"],
        ["3", "Acacia dealbata", "2020-05-01", "DatasetA"],
    ]
    db_dir = tmp_path / "Database"
    db_dir.mkdir()
    csv_path = db_dir / "new_flora.csv"
    write_csv(csv_path, header, rows)

    # Monkeypatch the module to read from our temp location
    monkeypatch.setattr(search_flora, "Path", Path)

    # Copy the temporary file to the expected relative location by adjusting __file__ dir
    # Simulate the module living inside tmp_path by changing __file__-based resolution
    monkeypatch.setattr(search_flora, "__file__", str(tmp_path / "search_flora.py"))

    # Case-insensitive search on "Scientific Name"
    results = search_flora.search_flora_database([
        ("acacia", "Scientific Name"),
    ])

    assert len(results) == 1 + 2  # header + 2 matches
    assert results[0] == header
    assert {r[0] for r in results[1:]} == {"1", "3"}


def test_search_flora_date_column_not_lowercased(tmp_path, monkeypatch):
    header = ["Occurrence ID", "Scientific Name", "Event Date", "Dataset Name"]
    rows = [["10", "Species X", "2020-01-02", "DS"]]
    db_dir = tmp_path / "Database"
    db_dir.mkdir()
    csv_path = db_dir / "new_flora.csv"
    write_csv(csv_path, header, rows)

    monkeypatch.setattr(search_flora, "__file__", str(tmp_path / "search_flora.py"))

    # Searching for exact substring without lowercasing for date column
    results = search_flora.search_flora_database([
        ("2020-01-02", "Event Date"),
    ])
    assert len(results) == 2
    assert results[1][0] == "10"


