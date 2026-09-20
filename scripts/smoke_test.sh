#!/usr/bin/env bash
# Phase 3 exit criterion. Must complete in under 60 seconds.
set -euo pipefail
echo "[1/5] importing package..."
python -c "import oran_ids; print('    ok')"
echo "[2/5] building synthetic 500-row corpus..."
python -c "import oran_ids.io as io; io.smoke_corpus(n=500)"
echo "[3/5] feature extraction + tiny model..."
python -c "import oran_ids.models as m; m.smoke_fit()"
echo "[4/5] metric computation..."
python -c "import oran_ids.metrics as k; k.smoke_metrics()"
echo "[5/5] determinism check (same seed twice -> identical output)..."
python -c "import oran_ids.io as io; assert io.smoke_determinism(), 'NONDETERMINISTIC'"
echo "SMOKE TEST PASSED"
