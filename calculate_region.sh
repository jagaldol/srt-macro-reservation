#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="/opt/homebrew/bin/python3"
fi

exec "$PYTHON" calculate_result_region.py "$@"
