#!/bin/sh
set -eu
BASE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
VER="0.70.1"
ARCHIVE="${1:-$BASE/frp_${VER}_linux_amd64.tar.gz}"
EXPECTED_ARCHIVE_SHA256="333da23d1b9009d7c01638e9ba38cf4600f7d37d393f854e96ee1396adefa9a6"
EXPECTED_FRPC_SHA256="7d0270753bd171566a5389d2709fea29d2151f8fb4066ac20947e548e1da193a"

[ -f "$ARCHIVE" ] || { echo "Missing $ARCHIVE" >&2; exit 1; }
ACTUAL="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[ "$ACTUAL" = "$EXPECTED_ARCHIVE_SHA256" ] || { echo "FRP archive SHA-256 mismatch" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
mkdir -p "$TMP/extract"
tar -xzf "$ARCHIVE" -C "$TMP/extract"
BIN="$(find "$TMP/extract" -type f -name frpc | head -n 1)"
[ -n "$BIN" ] || { echo "frpc not found in archive" >&2; exit 1; }
BIN_SHA256="$(sha256sum "$BIN" | awk '{print $1}')"
[ "$BIN_SHA256" = "$EXPECTED_FRPC_SHA256" ] || { echo "frpc binary SHA-256 mismatch" >&2; exit 1; }

cp "$BIN" "$BASE/package/bin/frpc"
chmod 755 "$BASE/package/bin/frpc"
"$BASE/build.sh" "frpc-x86_64-0.70.1-6-ui-launcher-fix.spk"
