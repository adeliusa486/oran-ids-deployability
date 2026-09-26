#!/usr/bin/env bash
# EXP-061 step 2: build FlexRIC v2.0.0 against the user-space SCTP/PCRE2 files.
set -euo pipefail
RIC=${RIC:-$HOME/ric}
L="$RIC/local/usr"
ML="$L/lib/x86_64-linux-gnu"
export PATH="$RIC/venv/bin:$PATH"
cd "$RIC/flexric"
git checkout -q v2.0.0
git rev-parse --short HEAD
rm -rf build && mkdir build && cd build
cmake .. -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_C_FLAGS="-I$L/include -Wno-error" \
  -DCMAKE_CXX_FLAGS="-I$L/include -Wno-error" \
  -DCMAKE_EXE_LINKER_FLAGS="-L$ML -Wl,-rpath,$ML" \
  -DCMAKE_SHARED_LINKER_FLAGS="-L$ML -Wl,-rpath,$ML" \
  -DCMAKE_LIBRARY_PATH="$ML" -DCMAKE_INCLUDE_PATH="$L/include" \
  -DPython3_EXECUTABLE="$RIC/venv/bin/python" \
  -DXAPP_MULTILANGUAGE=OFF 2>&1 | tail -8
ninja -j 16 2>&1 | tail -8
ls examples/ric/nearRT-RIC examples/emulator/agent/ 2>&1 | head
