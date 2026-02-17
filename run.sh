#!/usr/bin/env bash

set -euo pipefail

if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

python main.py \
  --start-hotkey "f9" \
  --stop-hotkey "esc" \
  --image-match-confidence 0.70 \
  --enable-waiting-list true \
  --roi-enabled true \
  --reservation-scan-timeout-sec 5 \
  --refresh-settle-delay-sec 0.18 \
  --enable-telegram-notification true
