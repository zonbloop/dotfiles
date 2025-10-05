#!/usr/bin/env bash
# Wrapper to run the memento mori generator and set wallpaper
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
python3 "$SCRIPT_DIR/memento_mori_v2.py"
