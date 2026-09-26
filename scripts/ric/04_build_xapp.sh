#!/usr/bin/env bash
# EXP-061 step 5: build the timing xApp inside the FlexRIC tree (it inherits the
# KPM/RC service-model definitions) and link ONNX Runtime 1.30.0 (C API), the
# version used on the Python side.
set -euo pipefail
RIC=${RIC:-$HOME/ric}
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC=${SRC:-$HERE/xapp_ids_timing}
ORT="$RIC/onnxruntime-linux-x64-1.30.0"
if [ ! -d "$ORT" ]; then
  cd "$RIC"
  curl -sSL -o ort.tgz "https://github.com/microsoft/onnxruntime/releases/download/v1.30.0/onnxruntime-linux-x64-1.30.0.tgz"
  tar xzf ort.tgz
fi
DST="$RIC/flexric/examples/xApp/c/ids_timing"
mkdir -p "$DST"
tr -d '\r' < "$SRC/xapp_ids_timing.c" > "$DST/xapp_ids_timing.c"
tr -d '\r' < "$SRC/CMakeLists.txt" > "$DST/CMakeLists.txt"
grep -q 'add_subdirectory(ids_timing)' "$RIC/flexric/examples/xApp/c/CMakeLists.txt" || \
  echo 'add_subdirectory(ids_timing)' >> "$RIC/flexric/examples/xApp/c/CMakeLists.txt"
export PATH="$RIC/venv/bin:$PATH"
cd "$RIC/flexric/build"
cmake .. -DORT_DIR="$ORT" > /dev/null
ninja xapp_ids_timing 2>&1 | grep -v 'executable stack' | tail -20
ls -la examples/xApp/c/ids_timing/xapp_ids_timing
