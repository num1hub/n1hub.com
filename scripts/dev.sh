#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENGINE_DIR="${REPO_ROOT}/apps/engine"
VENV_DIR="${ENGINE_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo ">>> N1Hub dev bootstrap (macOS/Linux)"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating Python virtual environment at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

echo "Upgrading pip + installing engine dependencies (editable + dev extras)"
python -m pip install --upgrade pip >/dev/null
pip install -e "${ENGINE_DIR}[dev]"

echo "Starting data services via docker compose..."
(cd "${REPO_ROOT}/infra" && docker compose up -d)

echo ""
echo "CapsuleStore Postgres: postgres://postgres:postgres@localhost:5432/n1hub"
echo "Redis events: redis://localhost:6379/0"
echo "FastAPI: http://127.0.0.1:8000"
echo "Interface: run 'pnpm dev' (root app) in a separate terminal."
echo ""
echo "Starting Uvicorn (Ctrl+C to stop)..."

cd "${ENGINE_DIR}"
exec "${VENV_DIR}/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
