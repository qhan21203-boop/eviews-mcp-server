"""
EViews MCP Server
Provides MCP tools to control EViews 9 via COM automation.
Must run with 32-bit Python because EViews 9 COM is 32-bit only.
"""
import sys
import os

# Ensure the server directory is on path
_server_dir = os.path.dirname(os.path.abspath(__file__))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from mcp.server.fastmcp import FastMCP
from eviews_client import get_client

mcp = FastMCP(
    name="EViews MCP Server",
    instructions="""Control EViews 9 (econometric software) via COM automation.

Available operations:
- Connect/disconnect/status management
- Create/open/save workfiles
- Import CSV data (via pandas + PutSeries)
- Run arbitrary EViews commands and programs
- Read/write scalars, series, and groups
- OLS regression with formatted coefficient output
- Get equation statistics (R², DW, F, N, etc.)
- Get equation coefficients with std errors and t-stats
- Freeze output views as tables and save to text files
- Look up objects in the workfile

Always connect first with eviews_connect before using other tools.
""",
)

# ═══════════════════════════════════════════════
# Connection management
# ═══════════════════════════════════════════════

@mcp.tool(description="Connect to EViews. Starts EViews if not running. Must call before any other EViews operation.")
def eviews_connect() -> str:
    client = get_client()
    if client.is_connected():
        return "Already connected to EViews."
    ok = client.connect()
    return "Connected to EViews." if ok else "Failed to connect. Is EViews 9 installed?"


@mcp.tool(description="Check EViews connection status.")
def eviews_status() -> str:
    client = get_client()
    if not client.is_connected():
        return "Not connected."
    return "Connected to EViews."


@mcp.tool(description="Disconnect from EViews.")
def eviews_disconnect() -> str:
    get_client().disconnect()
    return "Disconnected."


# ═══════════════════════════════════════════════
# Workfile operations
# ═══════════════════════════════════════════════

@mcp.tool(description="Create a new EViews workfile. page_type: 'u'=undated, 'a'=annual, 'q'=quarterly, 'm'=monthly. frequency: obs count (e.g. '100') or year range (e.g. '1990 2020').")
def eviews_create_workfile(page_type: str = "u", frequency: str = "100",
                           name: str = "untitled") -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.create_workfile(page_type, frequency, name)
        return f"Workfile created ({page_type}, {frequency} obs)."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Open an existing EViews workfile (.wf1). Provide the full file path.")
def eviews_open_workfile(filepath: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.open_workfile(filepath)
        return f"Opened: {filepath}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Save the current workfile. Optionally provide a new file path.")
def eviews_save_workfile(filepath: str = "") -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.save_workfile(filepath)
        return f"Saved: {filepath or '(current name)'}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Fetch an object from the EViews database into the workfile.")
def eviews_fetch(name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.fetch(name)
        return f"Fetched: {name}"
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════
# Run commands
# ═══════════════════════════════════════════════

@mcp.tool(description="Run a single EViews command. Examples: 'series y = x + 1', 'ls y c x', 'scalar m = @mean(x)'.")
def eviews_run(command: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.run(command)
        return f"OK: {command[:100]}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Run a multi-line EViews program. Lines starting with ' are comments.")
def eviews_run_program(program: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    results = client.run_program(program)
    return "\n".join(results)


# ═══════════════════════════════════════════════
# Data access
# ═══════════════════════════════════════════════

@mcp.tool(description="Get a scalar value from EViews by name.")
def eviews_get_scalar(name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        val = client.get(name)
        return f"{name} = {val}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Set a scalar value in EViews. Creates if it doesn't exist.")
def eviews_put_scalar(name: str, value: float) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.put(name, value)
        return f"{name} = {value}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Get values of a series as a list. Use after running commands like 'series y = x + 1'.")
def eviews_get_series(name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        data = client.get_series(name)
        if len(data) <= 50:
            return f"{name} ({len(data)} obs): {list(data)}"
        else:
            return f"{name} ({len(data)} obs). First 10: {list(data[:10])} ..."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Write values into an EViews series. Creates or overwrites the series.")
def eviews_put_series(name: str, values: str) -> str:
    """values: comma-separated numbers, e.g. '1,2,3,4,5'"""
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        data = [float(v.strip()) for v in values.split(",")]
        client.put_series(name, data)
        return f"Series '{name}' written with {len(data)} values."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Get data from an EViews group (multi-series). Returns row-wise tuples.")
def eviews_get_group(name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        data = client.get_group(name)
        if len(data) <= 20:
            return f"Group '{name}' ({len(data)} rows): {data}"
        else:
            return f"Group '{name}' ({len(data)} rows). First 5: {data[:5]} ..."
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════
# Object inspection
# ═══════════════════════════════════════════════

@mcp.tool(description="Look up an object in EViews. Returns its type (SERIES, SCALAR, EQUATION, GROUP, TABLE, GRAPH, etc.).")
def eviews_lookup(name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        obj_type = client.lookup(name)
        return f"{name}: {obj_type}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Show an EViews object view. Examples: 'x.line', 'eq1', 'tab1'.")
def eviews_show(view: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.show(view)
        return f"Showing: {view}"
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════
# CSV import (uses pandas + PutSeries to avoid EViews IMPORT issues)
# ═══════════════════════════════════════════════

@mcp.tool(description="Import CSV data into the current EViews workfile. Uses pandas to read CSV, then pushes data via PutSeries (avoids EViews IMPORT compatibility issues). Returns series count and row count.")
def eviews_import_csv(filepath: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        info = client.import_csv(filepath)
        return f"Imported {info['series_count']} series, {info['rows']} rows."
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════
# Equation / regression tools
# ═══════════════════════════════════════════════

@mcp.tool(description="Run an OLS regression. Specify equation name, dependent variable, and list of independent variables (space-separated). Example: ols('eq1', 'LNCO2', 'LNGDP LNEI LNCOAL')")
def eviews_ols(eq_name: str, dep_var: str, indep_vars: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        indep = indep_vars.strip().split()
        client.ols(eq_name, dep_var, indep)
        # Return key stats
        r2 = client.eq_attr(eq_name, "@r2")
        r2adj = client.eq_attr(eq_name, "@rbar2")
        dw = client.eq_attr(eq_name, "@dw")
        fstat = client.eq_attr(eq_name, "@f")
        n = client.eq_attr(eq_name, "@regobs")
        names = client.eq_varnames(eq_name)[1:]  # skip dep var
        coefs = client.eq_coefs(eq_name)
        tstats = client.eq_tstats(eq_name)
        lines = [f"OLS: {eq_name}.ls {dep_var} C {' '.join(indep)}"]
        lines.append(f"  R²={r2:.4f}  Adj R²={r2adj:.4f}  F={fstat:.4f}  DW={dw:.4f}  N={int(n)}")
        lines.append("  Coefficients:")
        for i, (v, c, t) in enumerate(zip(names, coefs, tstats)):
            lines.append(f"    {v:14s}  coef={c:12.6f}  t={t:10.4f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Get equation statistics: R², adj R², F, DW, N, ncoef. Provide equation name.")
def eviews_eq_stats(eq_name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        r2 = client.eq_attr(eq_name, "@r2")
        r2adj = client.eq_attr(eq_name, "@rbar2")
        fstat = client.eq_attr(eq_name, "@f")
        dw = client.eq_attr(eq_name, "@dw")
        n = client.eq_attr(eq_name, "@regobs")
        ncoef = client.eq_attr(eq_name, "@ncoef")
        return (
            f"{eq_name} stats:\n"
            f"  R² = {r2:.6f}\n"
            f"  Adj R² = {r2adj:.6f}\n"
            f"  F-stat = {fstat:.6f}\n"
            f"  Durbin-Watson = {dw:.6f}\n"
            f"  N = {int(n)}\n"
            f"  Coefficients = {int(ncoef)}"
        )
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Get equation coefficients with variable names, std errors, and t-statistics. Returns formatted table.")
def eviews_eq_coefficients(eq_name: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        names = client.eq_varnames(eq_name)[1:]  # skip dependent variable
        coefs = client.eq_coefs(eq_name)
        stderrs = client.eq_stderrs(eq_name)
        tstats = client.eq_tstats(eq_name)
        lines = [f"{'Variable':14s}  {'Coef':>14s}  {'Std.Err':>12s}  {'t-Stat':>10s}"]
        lines.append("-" * 58)
        for v, c, s, t in zip(names, coefs, stderrs, tstats):
            lines.append(f"  {v:12s}  {c:14.6f}  {s:12.6f}  {t:10.4f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════
# Output / table tools
# ═══════════════════════════════════════════════

@mcp.tool(description="Freeze an object's output view as a table. Examples: freeze('eq1') for equation output, freeze('tab_corr') for an existing table.")
def eviews_freeze(obj: str, table_name: str = "") -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        name = client.freeze_output(obj, table_name)
        return f"Frozen '{obj}' as table '{name}'."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool(description="Save a table to a text file. Example: save_table('ols_out', 'd:/output/ols_results.txt')")
def eviews_save_table(table_name: str, filepath: str) -> str:
    client = get_client()
    if not client.is_connected():
        return "Error: not connected."
    try:
        client.save_table(table_name, filepath)
        return f"Table '{table_name}' saved to: {filepath}"
    except Exception as e:
        return f"Error: {e}"


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
