#!/bin/sh
set -eu
BASE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
OUT="${1:-frpc-x86_64-0.70.1-6-ui-launcher-fix.spk}"

[ -x "$BASE/package/bin/frpc" ] || {
    echo "Missing executable package/bin/frpc" >&2
    exit 1
}

rm -f "$BASE/package.tgz" "$BASE/$OUT"
tar --owner=0 --group=0 --numeric-owner -czf "$BASE/package.tgz" -C "$BASE/package" .
MD5="$(md5sum "$BASE/package.tgz" | awk '{print $1}')"
sed "s/^checksum=.*/checksum=\"$MD5\"/" "$BASE/INFO.in" > "$BASE/INFO"
(
  cd "$BASE"
  tar --owner=0 --group=0 --numeric-owner -cf "$OUT" INFO package.tgz scripts PACKAGE_ICON.PNG
)
echo "$BASE/$OUT"
