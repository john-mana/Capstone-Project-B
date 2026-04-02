# conftest.py
import sys
import types
from pathlib import Path
import pytest

# Ensure repo root on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

if "tkinter" not in sys.modules:
    tk = types.ModuleType("tkinter")

    class _Widget:
        def __init__(self, *args, **kwargs):
            self._options = {}
            for k in ("text", "font", "bg", "fg"):
                if k in kwargs:
                    self._options[k] = kwargs[k]
        def pack(self, *a, **k): pass
        def grid(self, *a, **k): pass
        def grid_forget(self, *a, **k): pass
        def columnconfigure(self, *a, **k): pass
        def rowconfigure(self, *a, **k): pass
        def config(self, **k): self._options.update(k)
        configure = config
        def cget(self, key): return self._options.get(key, "")
        def bind(self, *a, **k): pass
        def update(self): pass
        def update_idletasks(self): pass

    class _Tk(_Widget):
        def title(self, *a, **k): pass
        def geometry(self, *a, **k): pass
        def configure(self, *a, **k): pass
        def withdraw(self): pass
        def deiconify(self): pass
        def mainloop(self): pass
        def protocol(self, *a, **k): pass
        def wait_window(self): pass
        def after(self, *a, **k): pass
        def destroy(self): pass
        def winfo_x(self): return 0
        def winfo_y(self): return 0
        def winfo_width(self): return 800
        def winfo_height(self): return 600

    tk.Tk = _Tk
    tk.Toplevel = _Tk
    tk.Frame = _Widget
    tk.LabelFrame = _Widget
    tk.Button = _Widget
    tk.Label = _Widget

    class _Scrollbar(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._command = None
        def config(self, **k):
            super().config(**k)
            if "command" in k: self._command = k["command"]
        configure = config
        def set(self, *a, **k): pass
    tk.Scrollbar = _Scrollbar

    class _Entry(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._buf = ""
        def delete(self, *a, **k): self._buf = ""
        def insert(self, _idx, s): self._buf += str(s)
        def get(self): return self._buf
    tk.Entry = _Entry

    class _Text(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._buf = ""
            self._state = "normal"
            self.yscrollcommand = k.get("yscrollcommand")
        def config(self, **k):
            super().config(**k)
            if "state" in k: self._state = k["state"]
        configure = config
        def delete(self, *a, **k): self._buf = ""
        def insert(self, _idx, s):
            if self._state != "disabled":
                self._buf += str(s)
        def get(self, *_): return self._buf
        def yview(self, *a, **k):
            if callable(self.yscrollcommand):
                self.yscrollcommand(0.0, 1.0)
    tk.Text = _Text

    class _Listbox(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._items = []
            self._selection = []
            self.yscrollcommand = k.get("yscrollcommand")
        def delete(self, *a, **k): self._items = []
        def insert(self, index, item): self._items.append(item)
        def curselection(self): return tuple(self._selection)
        def yview(self, *a, **k):
            if callable(self.yscrollcommand):
                self.yscrollcommand(0.0, 1.0)
    tk.Listbox = _Listbox

    # constants
    tk.NSEW = "nsew"; tk.W = "w"; tk.BOTH = "both"; tk.X = "x"
    tk.LEFT = "left"; tk.RIGHT = "right"; tk.TOP = "top"; tk.BOTTOM = "bottom"
    tk.CENTER = "center"
    tk.NORMAL = "normal"; tk.DISABLED = "disabled"
    tk.END = "end"; tk.WORD = "word"; tk.Y = "y"; tk.MULTIPLE = "multiple"
    # relief styles
    tk.SUNKEN = "sunken"; tk.RAISED = "raised"; tk.FLAT = "flat"
    tk.GROOVE = "groove"; tk.RIDGE = "ridge"

    class TclError(Exception): pass
    tk.TclError = TclError

    # tk variables: set sensible defaults so .get().strip() won't explode
    class _BaseVar:
        def __init__(self, value=None): self._v = value
        def get(self): return self._v
        def set(self, v): self._v = v
        def trace(self, *_): pass
    class StringVar(_BaseVar):
        def __init__(self, value=""): super().__init__(value)
    class IntVar(_BaseVar):
        def __init__(self, value=0): super().__init__(value)
    class DoubleVar(_BaseVar):
        def __init__(self, value=0.0): super().__init__(value)
    tk.StringVar = StringVar; tk.IntVar = IntVar; tk.DoubleVar = DoubleVar

    ttk = types.ModuleType("tkinter.ttk")
    ttk.Style = type("Style", (), {"__init__": lambda self, *a, **k: None,
                                   "theme_use": lambda self, *a, **k: None})

    class _Combobox(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._value = ""
            self._values = []
        def set(self, v): self._value = v
        def get(self): return self._value
        def __setitem__(self, key, val):
            if key == "values": self._values = list(val)
        def bind(self, *a, **k): pass
    ttk.Combobox = _Combobox

    class _Treeview(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._rows = {}
            self._order = []
            self._selection = []
            self._columns = k.get("columns", ())
            self.show = k.get("show", "")
            self.yscrollcommand = k.get("yscrollcommand")
        def insert(self, parent, index, text="", values=()):
            iid = f"iid{len(self._order)}"
            self._rows[iid] = {"text": text, "values": values}
            self._order.append(iid)
            return iid
        def delete(self, iid):
            if iid in self._rows:
                del self._rows[iid]
                self._order = [i for i in self._order if i != iid]
        def get_children(self, item=""): return tuple(self._order)
        def selection(self): return tuple(self._selection)
        def heading(self, *_a, **_k): pass
        def column(self, *_a, **_k): pass
        def item(self, iid, key=None):
            d = self._rows.get(iid, {})
            return d if key is None else d.get(key)
        def yview(self, *args, **kwargs):
            if callable(self.yscrollcommand):
                self.yscrollcommand(0.0, 1.0)
    ttk.Treeview = _Treeview

    class _Progressbar(_Widget):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.variable = k.get("variable")
            self.maximum = k.get("maximum", 100)
            self.length = k.get("length", 100)
    ttk.Progressbar = _Progressbar

    messagebox = types.ModuleType("tkinter.messagebox")
    messagebox.showinfo = lambda *a, **k: None
    messagebox.showwarning = lambda *a, **k: None
    messagebox.showerror = lambda *a, **k: None
    messagebox.askyesno = lambda *a, **k: True

    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.asksaveasfilename = lambda *a, **k: ""
    filedialog.askdirectory = lambda *a, **k: ""

    scrolledtext = types.ModuleType("tkinter.scrolledtext")
    class _ScrolledText(_Text): pass
    scrolledtext.ScrolledText = _ScrolledText

    sys.modules["tkinter"] = tk
    sys.modules["tkinter.ttk"] = ttk
    sys.modules["tkinter.messagebox"] = messagebox
    sys.modules["tkinter.filedialog"] = filedialog
    sys.modules["tkinter.scrolledtext"] = scrolledtext


def pytest_ignore_collect(path, config):
    if path.basename == "test_normalize_for_compare.py":
        try:
            import openpyxl  # noqa: F401
        except Exception:
            return True
    return False
