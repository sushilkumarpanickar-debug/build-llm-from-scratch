#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h:h}"
ICON_SOURCE="$REPO_ROOT/local_workspace/static/snns_emblem.png"
ICONSET="$SCRIPT_DIR/DAKSH/AppIcon.iconset"
ICNS="$SCRIPT_DIR/DAKSH/AppIcon.icns"

if [[ ! -f "$ICON_SOURCE" ]]; then
  echo "Missing DAKSH emblem at $ICON_SOURCE" >&2
  exit 1
fi

mkdir -p "$ICONSET"

sips -z 16 16 "$ICON_SOURCE" --out "$ICONSET/icon_16x16.png" >/dev/null
sips -z 32 32 "$ICON_SOURCE" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -z 32 32 "$ICON_SOURCE" --out "$ICONSET/icon_32x32.png" >/dev/null
sips -z 64 64 "$ICON_SOURCE" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -z 128 128 "$ICON_SOURCE" --out "$ICONSET/icon_128x128.png" >/dev/null
sips -z 256 256 "$ICON_SOURCE" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z 256 256 "$ICON_SOURCE" --out "$ICONSET/icon_256x256.png" >/dev/null
sips -z 512 512 "$ICON_SOURCE" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z 512 512 "$ICON_SOURCE" --out "$ICONSET/icon_512x512.png" >/dev/null
cp "$ICON_SOURCE" "$ICONSET/icon_512x512@2x.png"

xattr -cr "$ICONSET" >/dev/null 2>&1 || true
iconutil -c icns "$ICONSET" -o "$ICNS"
xattr -cr "$ICNS" >/dev/null 2>&1 || true
