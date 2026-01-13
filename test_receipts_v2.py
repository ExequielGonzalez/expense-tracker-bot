#!/usr/bin/env python3
"""
Comprehensive tests for multi-engine OCR receipt analyzer
Tests all 5 receipt images with confidence scoring validation
"""

import os
from receipt_analyzer_v2 import ReceiptAnalyzerV2

def print_separator(char='=', length=100):
    print(char * length)

def print_result_detail(result):
    """Print detailed analysis results"""
    if not result:
        print("  ❌ NO RESULT")
        return
    
    print(f"  💰 Amount: €{result['amount']:.2f} (confidence: {result['amount_confidence']}%)")
    print(f"  📅 Date: {result['date']} (confidence: {result['date_confidence']}%)")
    print(f"  🏪 Title: {result['title']} (confidence: {result['title_confidence']}%)")
    print(f"  📂 Category: {result['category']} (confidence: {result['category_confidence']}%)")
    print(f"  🎯 Overall Confidence: {result['overall_confidence']}%")
    print(f"  🔧 OCR Engine: {result['ocr_engine']} ({result['ocr_confidence']}%)")

def run_comprehensive_tests():
    """Run tests on all available receipt images"""
    
    # Initialize analyzer with all engines
    print("\n[INFO] Initializing Multi-Engine OCR Analyzer...")
    print("[INFO] Engines: Tesseract, EasyOCR, PaddleOCR")
    analyzer = ReceiptAnalyzerV2(engines=['tesseract', 'easyocr', 'paddleocr'])
    
    # Find all receipt images
    receipts_dir = 'data/receipts'
    receipt_files = sorted([f for f in os.listdir(receipts_dir) if f.endswith('.jpg')])
    
    print(f"[INFO] Found {len(receipt_files)} receipt images to analyze\n")
    
    # Test cases with expected values (if known)
    # Format: filename -> expected_data
    expected_data = {
        'receipt_20260109_155213.jpg': {
            'amount': 154.0,
            'date': '2024-11-12',  # No date visible
            'title_contains': 'SOLOPTICAL',
            'min_confidence': 50
        },
        'receipt_20260109_155314.jpg': {
            'amount': 3.5,
            'date': '2024-11-12',  # No date visible
            'title_contains': 'SOLOPTICAL',
            'min_confidence': 50
        },
        'receipt_20260109_191356.jpg': {
            'amount': 37.79,
            'date': '2026-01-09',  # No date visible
            'title_contains': 'ALDI',
            'min_confidence': 50
        },
        'receipt_20260109_191458.jpg': {
            'amount': 37.79,
            'date': '2026-01-09',  # No date visible
            'title_contains': 'ALDI',
            'min_confidence': 50
        },
        'receipt_20260109_191624.jpg': {
            'amount': 37.79,
            'date': '2026-01-09',  # No date visible
            'title_contains': 'ALDI',
            'min_confidence': 50
        },
            'receipt_20260109_215746.jpg': {
            'amount': 29.86,
            'date': '2026-01-07',  # No date visible
            'title_contains': 'GRUPO DIA',
            'min_confidence': 50
        }
    }
    
    print_separator()
    print("COMPREHENSIVE OCR TESTS - ALL RECEIPTS")
    print_separator()
    
    results = []
    passed = 0
    failed = 0
    
    for idx, filename in enumerate(receipt_files, 1):
        filepath = os.path.join(receipts_dir, filename)
        expected = expected_data.get(filename, {})
        
        print(f"\n[TEST {idx}/{len(receipt_files)}] {filename}")
        print_separator('-', 100)
        
        # Analyze receipt
        result = analyzer.analyze_receipt(filepath)
        
        if result:
            print_result_detail(result)
            
            # Validate against expected values
            test_passed = True
            reasons = []
            
            # Check confidence threshold
            min_conf = expected.get('min_confidence', 40)
            if result['overall_confidence'] < min_conf:
                test_passed = False
                reasons.append(f"Low confidence: {result['overall_confidence']}% < {min_conf}%")
            
            # Check expected amount if provided
            if 'amount' in expected:
                if abs(result['amount'] - expected['amount']) > 0.01:
                    test_passed = False
                    reasons.append(f"Amount mismatch: {result['amount']} != {expected['amount']}")
            
            # Check expected date if provided
            if 'date' in expected:
                if result['date'] != expected['date']:
                    test_passed = False
                    reasons.append(f"Date mismatch: {result['date']} != {expected['date']}")
            
            # Check title contains expected text
            if 'title_contains' in expected:
                if expected['title_contains'].lower() not in result['title'].lower():
                    test_passed = False
                    reasons.append(f"Title doesn't contain: {expected['title_contains']}")
            
            # Store result
            results.append({
                'filename': filename,
                'result': result,
                'passed': test_passed,
                'reasons': reasons
            })
            
            if test_passed:
                passed += 1
                print(f"\n  ✅ TEST PASSED")
            else:
                failed += 1
                print(f"\n  ❌ TEST FAILED")
                for reason in reasons:
                    print(f"     - {reason}")
        else:
            results.append({
                'filename': filename,
                'result': None,
                'passed': False,
                'reasons': ['No data extracted']
            })
            failed += 1
            print("  ❌ NO DATA EXTRACTED")
            print(f"\n  ❌ TEST FAILED")
    
    # Print summary
    print("\n")
    print_separator()
    print("SUMMARY REPORT")
    print_separator()
    print(f"\nTotal Tests: {len(receipt_files)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(receipt_files)*100):.1f}%")
    
    # Detailed results table
    print("\n")
    print_separator('-', 100)
    print(f"{'Receipt':<35} {'Amount':<12} {'Date':<12} {'Confidence':<12} {'Status':<10}")
    print_separator('-', 100)
    
    for r in results:
        filename = r['filename'][:33]
        if r['result']:
            res = r['result']
            amount = f"€{res['amount']:.2f}"
            date = res['date']
            confidence = f"{res['overall_confidence']}%"
            status = "✅ PASS" if r['passed'] else "❌ FAIL"
        else:
            amount = "N/A"
            date = "N/A"
            confidence = "0%"
            status = "❌ FAIL"
        
        print(f"{filename:<35} {amount:<12} {date:<12} {confidence:<12} {status:<10}")
    
    print_separator('-', 100)
    
    # Print confidence statistics
    if results:
        confidences = [r['result']['overall_confidence'] for r in results if r['result']]
        if confidences:
            print(f"\nConfidence Statistics:")
            print(f"  Average: {sum(confidences)/len(confidences):.1f}%")
            print(f"  Minimum: {min(confidences):.1f}%")
            print(f"  Maximum: {max(confidences):.1f}%")
    
    print("\n")
    print_separator()
    print(f"FINAL RESULT: {passed}/{len(receipt_files)} TESTS PASSED | {failed}/{len(receipt_files)} TESTS FAILED")
    print_separator()
    
    return failed == 0

def run_engine_comparison_test():
    """Compare performance of different OCR engines"""
    print("\n")
    print_separator()
    print("ENGINE COMPARISON TEST")
    print_separator()
    
    receipts_dir = 'data/receipts'
    test_file = os.path.join(receipts_dir, sorted(os.listdir(receipts_dir))[0])
    
    engines_to_test = [
        ['tesseract'],
        ['easyocr'],
        ['paddleocr'],
        ['tesseract', 'easyocr', 'paddleocr']
    ]
    
    print(f"\nTest image: {os.path.basename(test_file)}\n")
    
    for engines in engines_to_test:
        engine_name = '+'.join(engines) if len(engines) > 1 else engines[0]
        print(f"\n[{engine_name.upper()}]")
        print("-" * 50)
        
        analyzer = ReceiptAnalyzerV2(engines=engines)
        result = analyzer.analyze_receipt(test_file)
        
        if result:
            print(f"  Amount: €{result['amount']:.2f} (conf: {result['amount_confidence']}%)")
            print(f"  Title: {result['title']} (conf: {result['title_confidence']}%)")
            print(f"  Overall: {result['overall_confidence']}%")
            print(f"  Engine used: {result['ocr_engine']}")
        else:
            print("  ❌ Failed to extract data")
    
    print("\n")
    print_separator()

if __name__ == '__main__':
    # Run comprehensive tests
    success = run_comprehensive_tests()
    
    # Run engine comparison
    run_engine_comparison_test()
    
    exit(0 if success else 1)
