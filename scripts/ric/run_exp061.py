#!/usr/bin/env python3
"""EXP-061: decision loop of the radio detector through a live FlexRIC.

Runs the whole experiment from Windows through WSL2 (Ubuntu), in order:

  01_setup_toolchain.sh   cmake/ninja/swig in a venv, libsctp and pcre2 unpacked
                          from Ubuntu .deb files, FlexRIC cloned (no sudo needed)
  02_build_flexric.sh     FlexRIC v2.0.0, Release, SWIG bindings off
  export_radio_models.py  the six radio models of EXP-043 as verified ONNX files,
                          the held-out windows and reference scores (Windows side)
  04_build_xapp.sh        the timing xApp (xapp_ids_timing/) with ONNX Runtime 1.30.0
  05_run_exp061.sh        nearRT-RIC + emulated gNB + xApp per configuration
  analysis/ric_latency.py quantiles with distribution-free intervals

Run ALONE: concurrent jobs contaminate the tail. Takes about 15 minutes once the
toolchain is in place.

Usage:  python scripts/ric/run_exp061.py [--skip-build]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def wsl_path(p: Path) -> str:
    drive, rest = p.drive.rstrip(":").lower(), p.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{rest}"


def wsl(script: str, env: str = "") -> None:
    src = wsl_path(HERE / script)
    cmd = f"{env} bash <(tr -d '\\r' < '{src}')"
    print(f"  $ wsl {script}", flush=True)
    subprocess.run(["wsl", "-d", "Ubuntu", "--", "bash", "-lc", cmd], check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    a = ap.parse_args()
    if shutil.which("wsl") is None:
        print("EXP-061 needs WSL2 with an Ubuntu distribution; skipped, the "
              "committed results/EXP-061 files are used.")
        return 0
    if not a.skip_build:
        wsl("01_setup_toolchain.sh")
        wsl("02_build_flexric.sh")
    subprocess.run([sys.executable, str(HERE / "export_radio_models.py")], check=True)
    if not a.skip_build:
        wsl("04_build_xapp.sh", f"SRC='{wsl_path(HERE / 'xapp_ids_timing')}'")
    wsl("05_run_exp061.sh", f"REPO='{wsl_path(ROOT)}'")
    subprocess.run([sys.executable, str(ROOT / "analysis" / "ric_latency.py")], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
