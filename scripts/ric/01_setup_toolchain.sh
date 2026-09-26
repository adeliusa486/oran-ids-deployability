#!/usr/bin/env bash
# EXP-061 step 1: user-space toolchain for FlexRIC inside WSL2 (no sudo needed).
#   * cmake, ninja and swig from PyPI into a venv
#   * libsctp and pcre2 headers/libraries from Ubuntu's own .deb files, unpacked
#     into ~/ric/local with dpkg -x (apt-get download does not need root)
#   * FlexRIC cloned at a fixed tag
set -euo pipefail
RIC=${RIC:-$HOME/ric}
mkdir -p "$RIC/local" "$RIC/debs"
cd "$RIC"

if [ ! -x "$RIC/venv/bin/python" ]; then
  python3 -m venv "$RIC/venv" || { echo "venv module missing"; exit 2; }
fi
"$RIC/venv/bin/pip" install -q --upgrade pip
"$RIC/venv/bin/pip" install -q cmake ninja swig onnxruntime numpy
echo "cmake: $("$RIC/venv/bin/cmake" --version | head -1)"
echo "swig:  $("$RIC/venv/bin/swig" -version | grep -i version)"

cd "$RIC/debs"
apt-get download libsctp-dev libsctp1 libpcre2-dev libpcre2-8-0 libpcre2-16-0 libpcre2-32-0 libpcre2-posix3 2>&1 | tail -3 || true
for d in *.deb; do dpkg -x "$d" "$RIC/local"; done
ls "$RIC/local/usr/include/netinet/sctp.h" "$RIC/local/usr/include/pcre2.h"

cd "$RIC"
if [ ! -d flexric ]; then
  git clone -q https://gitlab.eurecom.fr/mosaic5g/flexric.git
fi
cd flexric
git fetch -q --tags
git tag | tail -5
