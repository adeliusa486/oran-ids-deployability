#!/usr/bin/env python3
"""Refresh the round-2 outputs that do not need the full statistics layer:
EXP-055 ladder and EXP-054 references -> EXP-052 processed, then numbers and
tables. Use analysis/revision_stats.py for the full run (bootstraps)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import revision_stats as r  # noqa: E402

if (r.RES / "EXP-055/raw/ladder_runs.csv").exists():
    r.published_ladder().to_csv(r.OUT / "published_ladder.csv", index=False)
if (r.RES / "EXP-054/raw/runs.csv").exists():
    r.target_reference().to_csv(r.OUT / "target_reference.csv", index=False)
for s in ("analysis/make_numbers.py", "analysis/make_tables_v2.py"):
    subprocess.run([sys.executable, str(ROOT / s)], check=True, cwd=ROOT,
                   stdout=subprocess.DEVNULL)
print("refreshed")
