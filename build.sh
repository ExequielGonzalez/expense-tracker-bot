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

echo "Select build configuration:"
echo ""
echo "  1) LIGHT   - Tesseract + EasyOCR (~2GB, 10-15 min build time)"
echo "  2) FULL    - All engines: Tesseract + EasyOCR + PaddleOCR (~4GB, 20-30 min)"
echo "  3) MINIMAL - Tesseract only (~100MB, 2-3 min) [Not recommended]"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "✅ Building LIGHT version (Tesseract + EasyOCR)..."
        # Already configured in Dockerfile (uses requirements-light.txt)
        docker compose build
        ;;
    2)
        echo "✅ Building FULL version (All 3 engines)..."
        # Temporarily modify Dockerfile to use full requirements
        sed -i.bak 's/requirements-light.txt/requirements.txt/' Dockerfile
        docker compose build
        # Restore original
        mv Dockerfile.bak Dockerfile
        ;;
    3)
        echo "⚠️  Building MINIMAL version (Tesseract only)..."
        echo "⚠️  This will disable EasyOCR and PaddleOCR fallback!"
        read -p "Continue? [y/N]: " confirm
        if [[ $confirm == [yY] ]]; then
            # Create minimal requirements
            cat > requirements-minimal.txt << EOF
python-telegram-bot==20.7
pytesseract==0.3.10
Pillow>=10.0.0
python-dotenv==1.0.0
opencv-python-headless>=4.8.0
scikit-image>=0.22.0
numpy>=1.24.0
EOF
            sed -i.bak 's/requirements-light.txt/requirements-minimal.txt/' Dockerfile
            docker compose build
            mv Dockerfile.bak Dockerfile
            rm requirements-minimal.txt
        else
            echo "❌ Build cancelled"
            exit 0
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Build Complete!                                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Run tests:    docker exec expense-tracker-bot python test_receipts_v2.py"
echo "  2. Start bot:    docker compose up -d"
echo "  3. View logs:    docker logs -f expense-tracker-bot"
echo ""
