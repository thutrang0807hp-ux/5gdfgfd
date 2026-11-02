#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
exec ../gflow-cli/.venv/bin/python app.py --open "$@"
