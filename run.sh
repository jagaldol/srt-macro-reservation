#!/usr/bin/env bash

# ensure UTF-8 locale for consistent output
default_locale="en_US.UTF-8"
if ! locale -a 2>/dev/null | grep -qi "^$"; then
  export LANG=C.UTF-8
  export LC_ALL=C.UTF-8
else
  export LANG=
  export LC_ALL=
fi

# activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

# run the app with any CLI overrides passed to this script
python main.py
