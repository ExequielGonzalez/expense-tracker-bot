#!/usr/bin/env bash
set -euo pipefail

REQ_FILE="/tmp/requirements.txt"
echo "Installing Python requirements from ${REQ_FILE}"
pip install --no-cache-dir -r "$REQ_FILE"

# Basic check
python -c "import sys; print('python', sys.version)"

echo "Dependencies installation complete."