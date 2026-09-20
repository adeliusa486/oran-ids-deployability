"""Put ``src/`` on ``sys.path`` for the whole test session.

Without this, ``pytest`` collects nothing importable: the package lives under
``src/`` and is not installed, so ``from oran_ids... import`` fails at collection.

The suite used to pass anyway, because ``experiments/final_validation.py`` sets
``PYTHONPATH=src`` when it shells out to pytest. That hid a real reproducibility
gap -- ``make test``, a bare ``pytest``, an IDE runner and a fresh clone all
failed, while the one command we used to check the repository's health passed.
A guard that only works when invoked through a single wrapper is not a guard.

Fixed here rather than by adding the wrapper's environment variable to more
places, so that every entry point behaves the same way.
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
