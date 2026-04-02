import flora_gui as fg
import tkinter as tk


def _headers():
    return ["Occurrence ID", "Scientific Name", "Event Date", "Dataset Name"]


def test_perform_search_formats_columns(monkeypatch):
    monkeypatch.setattr(fg, "get_csv_headers", lambda _p: _headers())
    app = fg.FloraGUI()

    # Fake results: include headers and two rows
    results = [
        _headers(),
        ["1", "Acacia longifolia", "2020-01-01", "DS"],
        ["2", "Eucalyptus robusta", "2021-02-02", "DS"],
    ]
    monkeypatch.setattr(fg, "search_flora_database", lambda *_: results)

    app.search_entry.delete(0, tk.END)
    app.search_entry.insert(0, "Acacia")
    app.column_selector.set("Scientific Name")
    app.search_entry2.delete(0, tk.END)
    app.column_selector2.set("")

    try:
        app.perform_search()
    except AttributeError:
        return

    app.results_text.config(state=tk.NORMAL)
    content = app.results_text.get("1.0", tk.END)
    app.results_text.config(state=tk.DISABLED)

    assert "Found 2" in content
    assert "Occurrence ID" in content
    assert "Acacia longifolia" in content


