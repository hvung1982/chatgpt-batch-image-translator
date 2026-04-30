#!/usr/bin/env bash
set -euo pipefail

APP_NAME="ChatGPT Batch Translator"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$ROOT/dist"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT"

echo "==> Using Python:"
"$PYTHON_BIN" -c 'import sys; print(sys.executable); raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'

echo "==> Checking Tkinter support..."
"$PYTHON_BIN" -c 'import tkinter; print(tkinter.Tcl().eval("info patchlevel"))'

echo "==> Installing Python dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt

echo "==> Cleaning old macOS build output..."
rm -rf "$ROOT/build" "$APP_BUNDLE"

echo "==> Building macOS .app with PyInstaller..."
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --collect-all playwright \
  --hidden-import run_chatgpt_batch \
  app.pyw

echo "==> Installing Playwright Chromium inside the app bundle..."
export PLAYWRIGHT_BROWSERS_PATH="$APP_BUNDLE/Contents/MacOS/ms-playwright"
"$PYTHON_BIN" -m playwright install chromium

echo "==> Done."
echo "App bundle:"
echo "$APP_BUNDLE"
echo
echo "First run note:"
echo "macOS may require right click > Open, or removing quarantine with:"
echo "xattr -dr com.apple.quarantine \"$APP_BUNDLE\""
