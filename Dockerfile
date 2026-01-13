FROM python:3.11-slim

ARG USE_GPU=0
ENV USE_GPU=${USE_GPU}

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install via helper script to attempt GPU installs when requested
COPY requirements-light.txt /tmp/requirements-light.txt
COPY requirements.txt /tmp/requirements.txt
COPY scripts/install_deps.sh /usr/local/bin/install_deps.sh
RUN chmod +x /usr/local/bin/install_deps.sh && /usr/local/bin/install_deps.sh

COPY . .

CMD ["python", "-u", "bot.py"]
