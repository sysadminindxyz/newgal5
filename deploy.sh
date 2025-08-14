#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3.12}"

$PYTHON_BIN -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# Token optional if using SSH in requirements.txt
if [[ -n "${GH_TOKEN:-}" ]]; then
  pip install -r requirements.txt || \
  pip install "git+https://${GH_TOKEN}@github.com/your-org/central-pipeline@v0.1.0#subdirectory=indxyz_utils"
else
  pip install -r requirements.txt
fi

exec python -m streamlit run test4.py
