# test/test_dataset_splitter_more.py
import os
import pandas as pd
import dataset_splitter as ds


# --- Small dummies we can reuse in multiple tests -------------------
class DummyVar:
    def __init__(self): self.v = None
    def set(self, v): self.v = v
    def get(self): return self.v

class DummyRoot:
    def after(self, *_a, **_k): pass
    def update(self): pass
    def update_idletasks(self): pass
    def destroy(self): pass
    def protocol(self, *a, **k): pass

class DummyLabel:
    def __init__(self): self.last = ""
    def config(self, **k):
        if "text" in k: self.last = k["text"]

class DummyListbox:
    def __init__(self):
        self._items = []
        self._sel = ()
    def delete(self, *_): self._items.clear()
    def insert(self, _i, item): self._items.append(item)
    def curselection(self): return self._sel
    def set_selection(self, sel): self._sel = tuple(sel)
    # layout no-ops
    def pack(self, *_, **__): pass

class DummyTree:
    def __init__(self):
        self.rows = {}
        self.order = []
        self._selection = ()
    def get_children(self):
        return tuple(self.order)
    def delete(self, iid):
        if iid in self.rows:
            del self.rows[iid]
            self.order = [x for x in self.order if x != iid]
    def insert(self, parent, index, text="", values=()):
        iid = f"iid{len(self.order)}"
        self.rows[iid] = {"text": text, "values": values}
        self.order.append(iid)
        return iid
    def selection(self):
        return self._selection
    def set_selection(self, ids):
        self._selection = tuple(ids)
    def item(self, iid, key=None):
        d = self.rows.get(iid, {})
        return d if key is None else d.get(key)
    def update(self): pass
    def update_idletasks(self): pass
    # layout no-ops
    def pack(self, *_, **__): pass


# --- Tests ----------------------------------------------------------

def test_load_dataset_success_populates_names_and_status(monkeypatch):
    splitter = ds.DatasetSplitter()

    # Inject light-weight UI parts
    splitter.dataset_listbox = DummyListbox()
    splitter.progress_var = DummyVar()
    splitter.status_label = DummyLabel()
    splitter.root = DummyRoot()

    # Pretend file exists and return a small dataframe
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    df = pd.DataFrame({"Dataset Name": ["A", "A", "B"], "v": [1, 2, 3]})
    monkeypatch.setattr(pd, "read_csv", lambda p: df)

    # capture showerror in case of unexpected issue
    called = {"err": False}
    import tkinter.messagebox as m
    monkeypatch.setattr(m, "showerror", lambda *a, **k: called.__setitem__("err", True))

    splitter.load_dataset()

    # No error dialog
    assert called["err"] is False
    # Names populated with counts in UI listbox
    assert len(splitter.dataset_listbox._items) == 2
    assert any("A (2 records)" in it for it in splitter.dataset_listbox._items)
    assert any("B (1 records)" in it for it in splitter.dataset_listbox._items)
    # Status updated
    assert "total records" in splitter.status_label.last.lower()


def test_split_datasets_cancelled_name_returns_early(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.original_data = pd.DataFrame({"Dataset Name": ["A", "B"], "x": [1, 2]})
    splitter.dataset_names = ["A", "B"]
    splitter.dataset_listbox = DummyListbox()
    splitter.dataset_listbox.set_selection([0])  # choose "A"
    splitter.progress_var = DummyVar()
    splitter.root = DummyRoot()
    splitter.status_label = None

    # Simulate cancel (None)
    monkeypatch.setattr(ds.DatasetSplitter, "get_custom_dataset_name", lambda *_: None)

    # No dialogs expected, just a clean return
    splitter.split_datasets()
    assert splitter.split_data_storage == {}


def test_update_results_display_renders_all(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()

    # Prime storage with two "custom" datasets
    splitter.split_data_storage = {
        "MergedAB": {"records": 3, "created": "12:00:00"},
        "OnlyB": {"records": 1, "created": "12:05:00"},
    }

    splitter.update_results_display()

    # Two rows with expected text/values
    assert len(splitter.results_tree.order) == 2
    texts = [splitter.results_tree.rows[i]["text"] for i in splitter.results_tree.order]
    vals = [splitter.results_tree.rows[i]["values"] for i in splitter.results_tree.order]
    assert "MergedAB" in texts and "OnlyB" in texts
    assert (3, "12:00:00") in vals and (1, "12:05:00") in vals


def test_download_selected_no_selection_warns(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()

    called = {"warn": False}
    import tkinter.messagebox as m
    monkeypatch.setattr(m, "showwarning", lambda *a, **k: called.__setitem__("warn", True))

    splitter.download_selected()
    assert called["warn"] is True


def test_download_selected_single_saves_to_file(tmp_path, monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()

    # Put one dataset into storage
    df = pd.DataFrame({"a": [1, 2]})
    name = "MergedAB"
    splitter.split_data_storage[name] = {"data": df, "records": 2, "created": "00:00:00"}

    # Simulate a selection with one item
    iid = splitter.results_tree.insert("", "end", text=name, values=(2, "00:00:00"))
    splitter.results_tree.set_selection([iid])

    # Return a file path to save
    target = tmp_path / "out.csv"
    import tkinter.filedialog as fd
    monkeypatch.setattr(fd, "asksaveasfilename", lambda **k: str(target))

    # Capture dialogs
    called = {"ok": False}
    import tkinter.messagebox as m
    monkeypatch.setattr(m, "showinfo", lambda *a, **k: called.__setitem__("ok", True))
    monkeypatch.setattr(m, "showerror", lambda *a, **k: called.__setitem__("ok", False))

    splitter.download_selected()

    assert target.exists()
    assert called["ok"] is True


def test_download_selected_multiple_saves_to_dir(tmp_path, monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()

    # Prepare two datasets
    for nm, recs in [("MergedA", 2), ("MergedB", 3)]:
        df = pd.DataFrame({"a": list(range(recs))})
        splitter.split_data_storage[nm] = {"data": df, "records": recs, "created": "09:00:00"}
        iid = splitter.results_tree.insert("", "end", text=nm, values=(recs, "09:00:00"))

    splitter.results_tree.set_selection(splitter.results_tree.get_children())

    # Directory selection returns tmp_path
    import tkinter.filedialog as fd
    monkeypatch.setattr(fd, "askdirectory", lambda **k: str(tmp_path))

    # Capture success
    called = {"ok": False}
    import tkinter.messagebox as m
    monkeypatch.setattr(m, "showinfo", lambda *a, **k: called.__setitem__("ok", True))

    splitter.download_selected()

    # Files exist with names derived from dataset names
    assert (tmp_path / "MergedA.csv").exists()
    assert (tmp_path / "MergedB.csv").exists()
    assert called["ok"] is True


def test_clear_selected_splits_warns_when_empty_selection(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()

    called = {"warn": False}
    import tkinter.messagebox as m
    monkeypatch.setattr(m, "showwarning", lambda *a, **k: called.__setitem__("warn", True))

    splitter.clear_selected_splits()
    assert called["warn"] is True


def test_clear_selected_splits_deletes_when_confirmed(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()
    splitter.update_status = lambda *_: None  # ignore status update text

    # add a row & storage
    splitter.split_data_storage["Merged"] = {"records": 1, "created": "00:00:00"}
    iid = splitter.results_tree.insert("", "end", text="Merged", values=(1, "00:00:00"))
    splitter.results_tree.set_selection([iid])

    import tkinter.messagebox as m
    monkeypatch.setattr(m, "askyesno", lambda *a, **k: True)

    splitter.clear_selected_splits()
    assert "Merged" not in splitter.split_data_storage


def test_clear_selected_splits_cancel_keeps_data(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()
    splitter.update_status = lambda *_: None

    splitter.split_data_storage["Merged"] = {"records": 1, "created": "00:00:00"}
    iid = splitter.results_tree.insert("", "end", text="Merged", values=(1, "00:00:00"))
    splitter.results_tree.set_selection([iid])

    import tkinter.messagebox as m
    monkeypatch.setattr(m, "askyesno", lambda *a, **k: False)

    splitter.clear_selected_splits()
    assert "Merged" in splitter.split_data_storage  # unchanged


def test_clear_all_splits_confirmed(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()
    splitter.update_status = lambda *_: None

    splitter.split_data_storage["X"] = {}
    splitter.split_data_storage["Y"] = {}

    import tkinter.messagebox as m
    monkeypatch.setattr(m, "askyesno", lambda *a, **k: True)

    splitter.clear_all_splits()
    assert splitter.split_data_storage == {}


def test_clear_all_splits_no_data_shows_info(monkeypatch):
    splitter = ds.DatasetSplitter()
    splitter.results_tree = DummyTree()

    called = {"info": False}
    import tkinter.messagebox as m
    monkeypatch.setattr(m, "showinfo", lambda *a, **k: called.__setitem__("info", True))

    splitter.clear_all_splits()
    assert called["info"] is True


def test_back_to_dashboard_calls_callback_and_clears(monkeypatch):
    flags = {"called": False}
    def cb(): flags["called"] = True

    splitter = ds.DatasetSplitter(dashboard_callback=cb)
    splitter.split_data_storage = {"a": 1}
    splitter.root = DummyRoot()

    splitter.back_to_dashboard()
    assert flags["called"] is True
    assert splitter.split_data_storage == {}
