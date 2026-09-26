#!/usr/bin/env bash
# EXP-063 step 1: Zeek 8.0 LTS (the Zeek project's own build for Ubuntu 24.04,
# openSUSE Build Service) unpacked into ~/zeek without sudo. Missing shared
# libraries are fetched from the host's Ubuntu archive with apt-get download.
set -euo pipefail
Z=${Z:-$HOME/zeek}
REPO=https://download.opensuse.org/repositories/security:/zeek/xUbuntu_24.04/amd64
mkdir -p "$Z/debs" "$Z/root"
cd "$Z/debs"
for p in zeek-lts-core_8.0.10-0_amd64.deb libbroker-lts-dev_8.0.10-0_amd64.deb; do
  [ -f "$p" ] || curl -sSfLO "$REPO/$p"
done
# shared libraries the Ubuntu 24.04 build expects and this host lacks
apt-get download libmaxminddb0 libzmq5 libsodium23 libpgm-5.3-0t64 libnorm1t64 >/dev/null 2>&1 || true
for d in *.deb; do dpkg -x "$d" "$Z/root"; done
ZEEK=$(find "$Z/root" -type f -name zeek -path '*bin*' | head -1)
echo "zeek binary: $ZEEK"
LIBS=$(find "$Z/root" -name '*.so*' -printf '%h\n' | sort -u | tr '\n' ':')
missing=$(LD_LIBRARY_PATH="$LIBS" ldd "$ZEEK" | awk '/not found/{print $1}')
echo "missing: ${missing:-none}"
for lib in $missing; do
  pkg=$(apt-file search -x "/$lib\$" 2>/dev/null | head -1 | cut -d: -f1 || true)
  echo "  $lib -> ${pkg:-?}"
done

# wrapper: the package is built for /opt/zeek, so point it at the relocated tree
cat > "$Z/zeek" <<WRAP
#!/usr/bin/env bash
R="$Z/root/opt/zeek"
export LD_LIBRARY_PATH="$LIBS\${LD_LIBRARY_PATH:-}"
export ZEEKPATH=".:\$R/share/zeek:\$R/share/zeek/policy:\$R/share/zeek/site:\$R/share/zeek/builtin-plugins"
export ZEEK_PLUGIN_PATH="\$R/lib/zeek/plugins"
exec "\$R/bin/zeek" "\$@"
WRAP
chmod +x "$Z/zeek"
"$Z/zeek" --version
