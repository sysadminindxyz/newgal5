#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SHA=8db92a2fe848129dada1148b8df3ecb36b7b79d8

PYTHON_BIN="${PYTHON_BIN:-python3.12}"

$PYTHON_BIN -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# Token optional if using SSH in requirements.txt
if [[ -n "${GH_TOKEN:-}" ]]; then
  pip install -r requirements.txt || \
  pip install "git+https://${GH_TOKEN}@github.com/sysadminindxyz/central-pipeline@$SHA#subdirectory=indxyz_utils"
else
  pip install -r requirements.txt
fi


