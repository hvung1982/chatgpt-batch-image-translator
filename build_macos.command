#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
chmod +x build_macos.sh
./build_macos.sh

echo
echo "Build finished. You can close this window."
read -r -p "Press Enter to close..."
