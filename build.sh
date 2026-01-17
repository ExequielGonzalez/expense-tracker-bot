#!/bin/bash

# Docker Build Script for Expense Tracker Bot
# Provides options for different build configurations

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Expense Tracker Bot - Docker Build Script               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    exit 1
fi

echo "Building docker image..."
docker compose build

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Build Complete!                                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Run tests:    docker exec expense-tracker-bot python test_receipts_v3.py --quick"
echo "  2. Start bot:    docker compose up -d"
echo "  3. View logs:    docker logs -f expense-tracker-bot"
echo ""
