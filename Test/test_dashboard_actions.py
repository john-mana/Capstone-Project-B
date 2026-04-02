
import dashboard


class DummyTk:
    def __init__(self):
        self.withdrawn = False
        self.deiconified = False
    def title(self, *_):
        pass
    def geometry(self, *_):
        pass
    def configure(self, **_):
        pass
    def pack(self, *_, **__):
        pass
    def grid(self, *_, **__):
        pass
    def withdraw(self):
        self.withdrawn = True
    def deiconify(self):
        self.deiconified = True
    def mainloop(self):
        pass


def test_open_flora_search_calls_child_and_returns(monkeypatch):
    import tkinter as tk
    monkeypatch.setattr(tk, "Tk", DummyTk)

    # Capture whether child run executed and dashboard callback called
    events = {"run": False, "callback": False}

    class FakeFlora:
        def __init__(self, dashboard_callback=None):
            self._cb = dashboard_callback
        def run(self):
            events["run"] = True
            if self._cb:
                events["callback"] = True
                self._cb()

    monkeypatch.setitem(__import__("sys").modules, "flora_gui", type("M", (), {"FloraGUI": FakeFlora}))

    d = dashboard.Dashboard()
    d.open_flora_search()

    assert events["run"] is True
    assert events["callback"] is True
    assert d.root.deiconified is True


def test_open_dataset_splitter_calls_child_and_returns(monkeypatch):
    import tkinter as tk
    monkeypatch.setattr(tk, "Tk", DummyTk)

    events = {"run": False, "callback": False}

    class FakeSplitter:
        def __init__(self, dashboard_callback=None):
            self._cb = dashboard_callback
        def run(self):
            events["run"] = True
            if self._cb:
                events["callback"] = True
                self._cb()

    monkeypatch.setitem(__import__("sys").modules, "dataset_splitter", type("M", (), {"DatasetSplitter": FakeSplitter}))

    d = dashboard.Dashboard()
    d.open_dataset_splitter()

    assert events["run"] is True
    assert events["callback"] is True
    assert d.root.deiconified is True


def test_placeholder_function_shows_info(monkeypatch):
    import tkinter as tk
    monkeypatch.setattr(tk, "Tk", DummyTk)
    called = {"info": False}
    import tkinter.messagebox as mbox
    monkeypatch.setattr(mbox, "showinfo", lambda *a, **k: called.__setitem__("info", True))

    d = dashboard.Dashboard()
    d.placeholder_function()
    assert called["info"] is True


