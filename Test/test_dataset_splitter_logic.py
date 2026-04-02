# test/test_dataset_splitter_logic.py
import pandas as pd
import dataset_splitter


class DummyTk:
    def __init__(self): pass
    def title(self, *_): pass
    def geometry(self, *_): pass
    def configure(self, **_): pass
    def config(self, **_): pass
    def protocol(self, *_): pass
    def after(self, *_args, **_kwargs): pass
    def update(self): pass
    def update_idletasks(self): pass
    def destroy(self): pass
    def pack(self, *_, **__): pass
    def grid(self, *_, **__): pass
    # when used as Scrollbar
    def set(self, *_, **__): pass


class DummyListbox:
    def __init__(self):
        self._items = []
        self._selection = []
    def pack(self, *_, **__): pass
    def grid(self, *_, **__): pass
    def delete(self, *_): self._items = []
    def insert(self, _index, item): self._items.append(item)
    def curselection(self): return tuple(self._selection)
    def set_selection(self, indices): self._selection = list(indices)
    # scrollbar will call this
    def yview(self, *_, **__): pass


class DummyTreeview:
    def __init__(self, *_, **__):
        self._rows = []
        self.yscrollcommand = None
    def pack(self, *_, **__): pass
    def heading(self, *_, **__): pass
    def column(self, *_, **__): pass
    def get_children(self): return list(range(len(self._rows)))
    def delete(self, _): self._rows = []
    def insert(self, *_args, **kwargs):
        text = kwargs.get("text")
        values = kwargs.get("values")
        self._rows.append((text, values))
    def selection(self): return []
    def item(self, *_args, **_kwargs): return {"text": ""}
    def update(self): pass
    def update_idletasks(self): pass
    def yview(self, *_, **__):
        if callable(self.yscrollcommand):
            self.yscrollcommand(0.0, 1.0)


def test_split_datasets_merges_selected(monkeypatch):
    import tkinter as tk
    from tkinter import ttk

    monkeypatch.setattr(tk, "Toplevel", DummyTk)
    monkeypatch.setattr(tk, "Frame", lambda *a, **k: DummyTk())
    monkeypatch.setattr(tk, "Button", lambda *a, **k: DummyTk())
    monkeypatch.setattr(tk, "Label", lambda *a, **k: DummyTk())
    # Scrollbar needs .config() and .set()
    monkeypatch.setattr(tk, "Scrollbar", lambda *a, **k: DummyTk())
    # Listbox needs .yview()
    monkeypatch.setattr(tk, "Listbox", lambda *a, **k: DummyListbox())

    # Treeview needs .yview()
    monkeypatch.setattr(ttk, "Treeview", lambda *a, **k: DummyTreeview())
    monkeypatch.setattr(ttk, "Progressbar", lambda *a, **k: DummyTk())

    splitter = dataset_splitter.DatasetSplitter()

    df = pd.DataFrame({
        "Dataset Name": ["A", "A", "B"],
        "Value": [1, 2, 3],
    })
    splitter.original_data = df
    splitter.dataset_names = ["A", "B"]

    assert isinstance(splitter.dataset_listbox, DummyListbox)
    splitter.dataset_listbox.set_selection([0, 1])

    monkeypatch.setattr(
        dataset_splitter.DatasetSplitter,
        "get_custom_dataset_name",
        lambda self, _: "MergedAB"
    )

    splitter.split_datasets()

    assert "MergedAB" in splitter.split_data_storage
    info = splitter.split_data_storage["MergedAB"]
    assert info["records"] == 3
