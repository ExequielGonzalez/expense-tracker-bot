FROM python:3.11-slim


RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
COPY scripts/install_deps.sh /usr/local/bin/install_deps.sh
RUN chmod +x /usr/local/bin/install_deps.sh && /usr/local/bin/install_deps.sh

COPY . .

CMD ["python", "-u", "bot.py"]
