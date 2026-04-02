from pathlib import Path
import csv
import search_flora


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def test_invalid_column_returns_empty(tmp_path, monkeypatch):
    header = ["A", "B"]
    rows = [["x", "y"]]
    db_dir = tmp_path / "Database"
    db_dir.mkdir()
    write_csv(db_dir / "new_flora.csv", header, rows)
    monkeypatch.setattr(search_flora, "__file__", str(tmp_path / "search_flora.py"))

    # Column not present
    results = search_flora.search_flora_database([("x", "MissingCol")])
    assert results == []


def test_missing_file_returns_empty(tmp_path, monkeypatch):
    # Point to non-existent base dir
    monkeypatch.setattr(search_flora, "__file__", str(tmp_path / "search_flora.py"))
    results = search_flora.search_flora_database([("x", "A")])
    assert results == []


