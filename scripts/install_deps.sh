#!/usr/bin/env bash
set -euo pipefail

echo "USE_GPU=${USE_GPU}"

# Prefer the provided requirements (full then light)
REQ_FILE="/tmp/requirements.txt"
if [ ! -f "$REQ_FILE" ]; then
  REQ_FILE="/tmp/requirements-light.txt"
fi

if [ "$USE_GPU" = "1" ]; then
  echo "Attempting GPU-accelerated installs (best-effort)..."

  # Attempt PyTorch with CUDA 11.8 (adjust if your host has a different CUDA)
  echo "Installing PyTorch (CUDA 11.8) via official index..."
  if ! pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu118 torch torchvision; then
    echo "PyTorch CUDA install failed, falling back to CPU torch..."
    pip install --no-cache-dir torch torchvision || true
  fi

  # Attempt paddlepaddle-gpu (best-effort). Paddle provides wheels on their site.
  echo "Attempting to install paddlepaddle-gpu (best-effort)..."
  if ! pip install --no-cache-dir paddlepaddle-gpu -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html; then
    echo "paddlepaddle-gpu install failed, installing paddlepaddle CPU package..."
    pip install --no-cache-dir paddlepaddle || true
  fi

  # Then install the rest of requirements without forcing paddle/torch versions
  echo "Installing remaining Python requirements from ${REQ_FILE} (skipping torch/paddle duplicates)..."
  # Filter out torch / paddle to avoid conflicts and install remaining packages
  FILTERED_PKGS=$(grep -viE "^(torch|torchvision|paddlepaddle|paddleocr)" "$REQ_FILE" || true)
  if [ -n "$FILTERED_PKGS" ]; then
    echo "$FILTERED_PKGS" | xargs -r pip install --no-cache-dir
  fi

  # Finally try to install paddleocr (depends on paddlepaddle)
  pip install --no-cache-dir paddleocr || echo "paddleocr install failed; continuing"
else
  echo "Installing CPU requirements from ${REQ_FILE}"
  pip install --no-cache-dir -r "$REQ_FILE"
fi

# Basic check
python -c "import sys; print('python', sys.version)"

echo "Dependencies installation complete."