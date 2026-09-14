#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h}"
ICON_SOURCE="$REPO_ROOT/local_workspace/static/snns_emblem.png"
PROJECT="$REPO_ROOT/macos/DAKSH/DAKSH.xcodeproj"
BUILD_ROOT="$REPO_ROOT/macos/DAKSH/build"
DERIVED_DATA="$BUILD_ROOT/DerivedData"
APP_SOURCE="$DERIVED_DATA/Build/Products/Release/DAKSH.app"
OUTPUT_DIR="${DAKSH_OUTPUT_DIR:-$REPO_ROOT/dist}"

mkdir -p "$OUTPUT_DIR"

xattr -cr "$ICON_SOURCE" >/dev/null 2>&1 || true
/bin/zsh "$REPO_ROOT/macos/DAKSH/generate_app_icon.sh"

xcodebuild \
  -project "$PROJECT" \
  -scheme DAKSH \
  -configuration Release \
  -derivedDataPath "$DERIVED_DATA" \
  CODE_SIGNING_ALLOWED=NO \
  build

ditto "$APP_SOURCE" "$OUTPUT_DIR/DAKSH.app"
xattr -cr "$OUTPUT_DIR/DAKSH.app" >/dev/null 2>&1 || true
codesign --force --deep --sign - "$OUTPUT_DIR/DAKSH.app" >/dev/null 2>&1 || true
ditto -c -k --sequesterRsrc --keepParent "$OUTPUT_DIR/DAKSH.app" "$OUTPUT_DIR/DAKSH-macOS-app.zip"

echo "Built $OUTPUT_DIR/DAKSH.app"
echo "Packaged $OUTPUT_DIR/DAKSH-macOS-app.zip"
