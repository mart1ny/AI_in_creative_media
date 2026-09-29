#!/usr/bin/env python3
"""Execute plain Python notebook cells with the standard library and save outputs.

Run from LR1_1 with ``.venv/bin/python notebooks/run_notebook.py``. The notebook
contains no IPython magics, so the same cells also work in Jupyter.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/LR01_variant3.ipynb"
LOG = ROOT / "reports/notebook_run.log"


def main() -> int:
    os.chdir(ROOT)
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    lines = [
        f"started_utc: {datetime.now(timezone.utc).isoformat()}",
        f"interpreter: {sys.executable}",
        f"notebook: {NOTEBOOK.relative_to(ROOT)}",
    ]
    count = 0
    for index, cell in enumerate(notebook["cells"], 1):
        if cell["cell_type"] != "code":
            continue
        count += 1
        source = "".join(cell["source"])
        output = io.StringIO()
        error = None
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                exec(compile(source, f"{NOTEBOOK.name}:cell-{index}", "exec"), namespace)
            except Exception:
                error = traceback.format_exc()
        text = output.getvalue()
        cell["execution_count"] = count
        cell["outputs"] = []
        if text:
            cell["outputs"].append({"output_type": "stream", "name": "stdout", "text": text.splitlines(keepends=True)})
        if error:
            cell["outputs"].append({"output_type": "error", "ename": "CellExecutionError", "evalue": error.splitlines()[-1], "traceback": error.splitlines()})
        lines.extend([f"\n--- cell {index} execution {count} ---", source.rstrip(), "--- output ---", text.rstrip()])
        if error:
            lines.append(error)
        NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if error:
            print(f"Cell {index} failed; see {LOG}", file=sys.stderr)
            return 1
    lines.append(f"\nfinished_utc: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"status: success; executed_cells: {count}")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Executed {count} cells successfully: {NOTEBOOK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
