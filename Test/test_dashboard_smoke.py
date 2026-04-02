import types
import builtins
import dashboard


class DummyTk:
    def __init__(self):
        self._withdrawn = False
        self._deiconified = False

    def pack(self, *_, **__):
        pass

    def grid(self, *_, **__):
        pass

    def title(self, *_):
        pass

    def geometry(self, *_):
        pass

    def configure(self, **_):
        pass

    def withdraw(self):
        self._withdrawn = True

    def deiconify(self):
        self._deiconified = True

    def mainloop(self):
        pass


def test_dashboard_instantiation_monkeypatched_tk(monkeypatch):
    # Monkeypatch tk.Tk used inside dashboard.Dashboard
    import tkinter as tk
    monkeypatch.setattr(tk, "Tk", DummyTk)

    d = dashboard.Dashboard()
    assert isinstance(d, dashboard.Dashboard)


