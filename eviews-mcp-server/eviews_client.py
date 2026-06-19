"""
EViews COM Automation Client Wrapper
Uses 32-bit Python - EViews 9 requires 32-bit COM client.
"""
import pythoncom
import win32com.client
import ctypes
from win32com.client import gencache
from typing import Any, Optional, List, Tuple

# Initialize COM once at module load
try:
    pythoncom.CoInitialize()
except:
    pass


class EViewsClient:
    """Manages connection to EViews via COM automation (32-bit)."""

    def __init__(self):
        self._mgr: Any = None
        self._app: Any = None
        self._connected: bool = False

    def connect(self) -> bool:
        """Connect to EViews via COM. Starts EViews if not running."""
        if self._connected and self._app is not None:
            try:
                self._app.Lookup("c")
                return True
            except:
                self._connected = False
                self._app = None
                self._mgr = None
        try:
            self._mgr = gencache.EnsureDispatch("EViews.Manager.9")
            self._app = self._mgr.GetApplication(0)
            self._connected = True
            self._show_window()
            return True
        except Exception:
            self._connected = False
            return False

    def _show_window(self):
        """Bring EViews main window to foreground."""
        import time
        for _ in range(10):
            time.sleep(0.5)
            hwnd = ctypes.windll.user32.FindWindowW(None, "EViews")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                return

    def disconnect(self):
        self._connected = False
        self._app = None
        self._mgr = None

    def is_connected(self) -> bool:
        return self._connected and self._app is not None

    @property
    def app(self):
        if not self._connected:
            raise RuntimeError("Not connected to EViews. Call connect() first.")
        return self._app

    def run(self, command: str) -> str:
        self._app.Run(command)
        return "OK"

    def run_program(self, program: str) -> List[str]:
        results = []
        for line in program.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("'"):
                continue
            try:
                self._app.Run(line)
                results.append(f"OK: {line[:80]}")
            except Exception as e:
                results.append(f"ERROR: {line[:80]} -> {e}")
        return results

    def put(self, name: str, value: float) -> None:
        self._app.Put(name, float(value))

    def get(self, name: str) -> float:
        return self._app.Get(name)

    def get_series(self, name: str) -> Tuple[float, ...]:
        result = self._app.GetSeries(name)
        return tuple(result) if result else ()

    def put_series(self, name: str, data: List[float]) -> None:
        self._app.PutSeries(name, list(data))

    def get_group(self, name: str) -> List[Tuple[float, ...]]:
        result = self._app.GetGroup(name)
        if result:
            return [tuple(row) for row in result]
        return []

    def lookup(self, name: str) -> str:
        return str(self._app.Lookup(name))

    def create_workfile(self, page_type: str = "u", freq: str = "100",
                        name: str = "untitled") -> None:
        try:
            self._app.Run("close")
        except:
            pass
        self._app.Run(f"wfcreate {page_type} {freq}")

    def open_workfile(self, path: str) -> None:
        self._app.Run(f'wfopen "{path}"')

    def save_workfile(self, path: str = "") -> None:
        if path:
            self._app.Run(f'wfsave "{path}"')
        else:
            self._app.Run("wfsave")

    def fetch(self, name: str) -> str:
        self._app.Run(f"fetch {name}")

    def show(self, view: str) -> None:
        self._app.Show(view)

    # ------------------------------------------------------------------
    # Equation / statistical helpers (from connect_eviews.py findings)
    # ------------------------------------------------------------------
    def ols(self, eq_name: str, dep: str, indep: list) -> None:
        """Run OLS regression: eq_name.ls dep C indep1 indep2 ..."""
        rhs = " ".join(indep)
        self._app.Run(f"equation {eq_name}.ls {dep} C {rhs}")
        import time
        time.sleep(0.5)

    def eq_attr(self, eq_name: str, attr: str):
        """Get equation statistic (e.g. @r2, @rbar2, @f, @dw, @regobs, @ncoef)."""
        return self._app.Get(f"{eq_name}.{attr}")

    def eq_coefs(self, eq_name: str):
        """Get all coefficients as a tuple."""
        return tuple(self._app.Get(f"{eq_name}.@coefs"))

    def eq_stderrs(self, eq_name: str):
        """Get all standard errors as a tuple."""
        return tuple(self._app.Get(f"{eq_name}.@stderrs"))

    def eq_tstats(self, eq_name: str):
        """Get all t-statistics as a tuple."""
        return tuple(self._app.Get(f"{eq_name}.@tstats"))

    def eq_varnames(self, eq_name: str) -> list:
        """Get equation variable names as list (first is dependent var)."""
        s = self._app.Get(f"{eq_name}.@varlist")
        return s.split() if isinstance(s, str) else []

    def freeze_output(self, obj: str, name: str = ""):
        """Freeze object output as a table."""
        n = name or f"{obj}_out"
        self._app.Run(f"freeze({n}) {obj}.output")
        import time
        time.sleep(0.5)
        return n

    def save_table(self, table_name: str, path: str):
        """Save a frozen table to a text file."""
        self._app.Run(f'{table_name}.save(t=txt) "{path}"')

    def import_csv(self, path: str) -> dict:
        """Import CSV data via stdlib csv + PutSeries.
        No pandas dependency — works with any Python.
        Returns dict with 'series_count' and 'rows'.
        """
        import csv
        import time as _time

        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return {"series_count": 0, "rows": 0}

        # Detect numeric columns: try to float-cast the first non-empty value
        numeric_cols = []
        for col in reader.fieldnames:
            for row in rows:
                v = row[col].strip()
                if v and v.upper() != "NA" and v != "#NA":
                    try:
                        float(v)
                        numeric_cols.append(col)
                    except ValueError:
                        pass
                    break  # only test first valid value

        for col in numeric_cols:
            vals = []
            for row in rows:
                v = row[col].strip()
                if not v or v.upper() == "NA" or v == "#NA":
                    vals.append(0.0)
                else:
                    try:
                        vals.append(float(v))
                    except ValueError:
                        vals.append(0.0)
            self._app.Run(f"series {col}")
            _time.sleep(0.05)
            self._app.PutSeries(col, tuple(vals))

        return {"series_count": len(numeric_cols), "rows": len(rows)}

    def put_group(self, *names_and_data):
        """Write group data to EViews."""
        self._app.PutGroup(*names_and_data)


_client: Optional[EViewsClient] = None


def get_client() -> EViewsClient:
    global _client
    if _client is None or not _client.is_connected():
        _client = EViewsClient()
    return _client
