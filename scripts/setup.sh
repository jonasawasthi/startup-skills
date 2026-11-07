#!/usr/bin/env bash
# Create the toolkit virtual environment and install dependencies.
set -euo pipefail
ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
"$PY" -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install -q --upgrade pip
"$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
if [ "${WITH_DEV:-1}" = "1" ]; then "$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements-dev.txt"; fi
"$ROOT/bin/startup-kit" doctor
