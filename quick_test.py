#!/usr/bin/env python3
"""
Quick test script to verify OCR functionality with single engine (Tesseract only)
Use this to test without building full Docker image with all engines
"""

import sys
import os

# Check if we're running in minimal environment
try:
    from receipt_analyzer_v2 import ReceiptAnalyzerV2
    print("[INFO] Using receipt_analyzer_v2 (multi-engine)")
    USE_V2 = True
except ImportError as e:
    print(f"[WARN] Cannot import v2 analyzer: {e}")
    print("[INFO] Falling back to receipt_analyzer (Tesseract only)")
    from receipt_analyzer import ReceiptAnalyzer
    USE_V2 = False

def test_single_receipt():
    """Test analysis on a single receipt"""
    
    receipts_dir = 'data/receipts'
    if not os.path.exists(receipts_dir):
        print(f"[ERROR] Directory not found: {receipts_dir}")
        return False
    
    receipt_files = sorted([f for f in os.listdir(receipts_dir) if f.endswith('.jpg')])
    
    if not receipt_files:
        print(f"[ERROR] No receipt images found in {receipts_dir}")
        return False
    
    test_file = os.path.join(receipts_dir, receipt_files[0])
    print(f"\n[INFO] Testing with: {receipt_files[0]}")
    print("=" * 80)
    
    if USE_V2:
        # Use multi-engine analyzer (only Tesseract in minimal env)
        analyzer = ReceiptAnalyzerV2(engines=['tesseract'])
        result = analyzer.analyze_receipt(test_file)
        
        if result:
            print(f"\n✅ ANALYSIS SUCCESSFUL")
            print(f"   Amount: €{result['amount']:.2f} (confidence: {result['amount_confidence']}%)")
            print(f"   Date: {result['date']} (confidence: {result['date_confidence']}%)")
            print(f"   Title: {result['title']} (confidence: {result['title_confidence']}%)")
            print(f"   Category: {result['category']} (confidence: {result['category_confidence']}%)")
            print(f"   Overall: {result['overall_confidence']}%")
            print(f"   Engine: {result['ocr_engine']}")
            return True
        else:
            print("\n❌ ANALYSIS FAILED - No data extracted")
            return False
    else:
        # Use legacy analyzer
        analyzer = ReceiptAnalyzer()
        result = analyzer.analyze_receipt(test_file)
        
        if result:
            print(f"\n✅ ANALYSIS SUCCESSFUL (Legacy)")
            print(f"   Amount: €{result['amount']:.2f}")
            print(f"   Date: {result['date']}")
            print(f"   Title: {result['title']}")
            return True
        else:
            print("\n❌ ANALYSIS FAILED - No data extracted")
            return False

if __name__ == '__main__':
    print("[INFO] Quick OCR Test Script")
    print("[INFO] This tests OCR functionality with available engines\n")
    
    success = test_single_receipt()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ OCR system is working!")
    else:
        print("❌ OCR system needs attention")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
