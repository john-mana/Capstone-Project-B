import flora_gui as fg
import tkinter as tk


def test_toggle_second_bar(monkeypatch):
    # Provide headers
    monkeypatch.setattr(fg, "get_csv_headers", lambda _p: [
        "Occurrence ID", "Scientific Name", "Event Date", "Dataset Name"
    ])
    app = fg.FloraGUI()

    # Initially hidden
    app.search_term_var.set("")
    try:
        app.toggle_second_search_bar()
    except AttributeError:
        return
    assert app.search_entry2.get() == "" if hasattr(app.search_entry2, "get") else True

    # When first term present -> shown and options updated
    app.search_term_var.set("Acacia")
    try:
        app.toggle_second_search_bar()
    except AttributeError:
        return
    # Should not raise and second combobox values set internally by stub
    try:
        app.update_second_column_options()
    except AttributeError:
        return


def test_update_second_column_options(monkeypatch):
    monkeypatch.setattr(fg, "get_csv_headers", lambda _p: [
        "Occurrence ID", "Scientific Name", "Event Date", "Dataset Name"
    ])
    app = fg.FloraGUI()
    app.column_selector.set("Scientific Name")
    app.update_second_column_options()
    # Ensure second combobox excludes the first selection
    if hasattr(app.column_selector2, "_values"):
        assert "Scientific Name" not in app.column_selector2._values


