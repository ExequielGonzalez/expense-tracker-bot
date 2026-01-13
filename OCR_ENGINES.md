# OCR Engines Configuration

## Available Engines

This project supports **3 OCR engines** with automatic fallback:

1. **Tesseract OCR** (Fast, lightweight, good for clear text)
2. **EasyOCR** (Better with difficult/blurry images, requires PyTorch)
3. **PaddleOCR** (Excellent for structured documents, requires PaddlePaddle)

## Installation Options

### Option 1: Full Installation (All 3 engines)

**Requirements:** ~4GB disk space, 8GB RAM recommended

```bash
pip install -r requirements.txt
```

**Note:** This installs PyTorch (~2GB) and PaddlePaddle (~500MB). Build time: 10-20 minutes.

### Option 2: Light Installation (Tesseract + EasyOCR)

**Requirements:** ~2GB disk space, 4GB RAM

```bash
pip install -r requirements-light.txt
```

**Note:** This installs PyTorch for EasyOCR. Build time: 5-10 minutes.

### Option 3: Minimal Installation (Tesseract only)

**Requirements:** ~100MB disk space, 2GB RAM

```bash
pip install python-telegram-bot==20.7
pip install pytesseract==0.3.10
pip install Pillow>=10.0.0
pip install python-dotenv==1.0.0
pip install opencv-python-headless>=4.8.0
pip install scikit-image>=0.22.0
pip install numpy>=1.24.0
```

**Note:** Fastest installation, uses only Tesseract. Build time: 1-2 minutes.

## Docker Configuration

### Full Docker Image (all engines)

```bash
docker compose build
```

This may take 15-30 minutes due to heavy dependencies.

### Light Docker Image (recommended)

Modify `Dockerfile` to use `requirements-light.txt`:

```dockerfile
COPY requirements-light.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
```

Then build:

```bash
docker compose build
```

Build time: 5-10 minutes.

## Engine Selection in Code

The analyzer automatically initializes available engines:

```python
# Try all engines
analyzer = ReceiptAnalyzerV2(engines=['tesseract', 'easyocr', 'paddleocr'])

# Use only Tesseract and EasyOCR
analyzer = ReceiptAnalyzerV2(engines=['tesseract', 'easyocr'])

# Use only Tesseract (fastest)
analyzer = ReceiptAnalyzerV2(engines=['tesseract'])
```

The system will gracefully fallback if an engine is not available.

## Performance Comparison

| Engine | Speed | Accuracy | Memory | Disk Space |
|--------|-------|----------|---------|------------|
| Tesseract | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 100MB | ~50MB |
| EasyOCR | ⚡⚡ Medium | ⭐⭐⭐⭐ Very Good | 2GB | ~2GB |
| PaddleOCR | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent | 4GB | ~4GB |

## Recommendations

- **For production:** Use Light installation (Tesseract + EasyOCR)
- **For development/testing:** Use Minimal installation (Tesseract only)
- **For maximum accuracy:** Use Full installation (all 3 engines)

## Troubleshooting

**Docker build times out:**
- Use requirements-light.txt instead
- Increase Docker memory to 8GB
- Build without cache: `docker compose build --no-cache`

**Out of memory errors:**
- Use fewer engines
- Increase swap space
- Use minimal installation

**EasyOCR/PaddleOCR not found:**
- The system will automatically fallback to Tesseract
- No action needed, but you'll miss the extra accuracy
