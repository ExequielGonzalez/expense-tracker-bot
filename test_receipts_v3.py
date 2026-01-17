#!/usr/bin/env python3
"""
Integration tests for ReceiptAnalyzerV3 (Ollama Vision LLM)

These tests run against real receipt images using the Ollama API.
They are designed to FAIL HARD if:
- Ollama is not running or unreachable
- The model returns invalid JSON
- Required fields are missing or invalid
- Category is not in the allowed set

Environment variables:
- OLLAMA_BASE_URL: Ollama API URL (default: http://localhost:11434)
- OLLAMA_MODEL: Model name (default: qwen3-vl:4b-instruct)
- OLLAMA_TIMEOUT: Request timeout in seconds (default: 120)

Usage:
    python test_receipts_v3.py              # Run all tests
    python test_receipts_v3.py --quick      # Run only first 2 images
    python test_receipts_v3.py --verbose    # Show raw model responses
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Set STORE_RAW_TEXT for verbose mode before importing analyzer
if '--verbose' in sys.argv:
    os.environ['STORE_RAW_TEXT'] = '1'

from receipt_analyzer_v3 import ReceiptAnalyzerV3, VALID_CATEGORIES


def print_separator(char='=', length=100):
    print(char * length)


def print_result_detail(result, verbose=False):
    """Print detailed analysis results"""
    if not result:
        print("  ❌ NO RESULT")
        return
    
    print(f"  💰 Amount: €{result['amount']:.2f} (confidence: {result['amount_confidence']}%)")
    print(f"  📅 Date: {result['date']} (confidence: {result['date_confidence']}%)")
    print(f"  🏪 Title: {result['title']} (confidence: {result['title_confidence']}%)")
    print(f"  📂 Category: {result['category']} (confidence: {result['category_confidence']}%)")
    print(f"  🎯 Overall Confidence: {result['overall_confidence']}%")
    print(f"  🤖 Model: {result.get('model', 'unknown')}")
    
    if verbose and result.get('raw_text'):
        print(f"\n  📝 Raw model response:")
        print(f"  {result['raw_text'][:500]}...")


def validate_result(result, filename):
    """
    Strictly validate the analysis result.
    
    Raises AssertionError if any validation fails.
    """
    assert result is not None, f"Analysis returned None for {filename}"
    
    # Validate amount
    assert 'amount' in result, f"Missing 'amount' field for {filename}"
    assert isinstance(result['amount'], (int, float)), f"Invalid amount type for {filename}"
    assert result['amount'] >= 0, f"Negative amount for {filename}: {result['amount']}"
    assert result['amount'] < 100000, f"Unreasonable amount for {filename}: {result['amount']}"
    
    # Validate date format
    assert 'date' in result, f"Missing 'date' field for {filename}"
    date_str = result['date']
    assert isinstance(date_str, str), f"Invalid date type for {filename}"
    
    if date_str != '1900-01-01':
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
            assert parsed_date.year >= 2020, f"Date year too old for {filename}: {date_str}"
        except ValueError:
            raise AssertionError(f"Invalid date format for {filename}: {date_str}")
    
    # Validate category - STRICT
    assert 'category' in result, f"Missing 'category' field for {filename}"
    assert result['category'] in VALID_CATEGORIES, \
        f"Invalid category for {filename}: '{result['category']}'. Must be one of {VALID_CATEGORIES}"
    
    # Validate title
    assert 'title' in result, f"Missing 'title' field for {filename}"
    assert isinstance(result['title'], str), f"Invalid title type for {filename}"
    assert len(result['title']) > 0, f"Empty title for {filename}"
    
    # Validate confidence scores
    for conf_field in ['amount_confidence', 'date_confidence', 'title_confidence', 
                       'category_confidence', 'overall_confidence']:
        assert conf_field in result, f"Missing '{conf_field}' field for {filename}"
        conf_value = result[conf_field]
        assert isinstance(conf_value, (int, float)), f"Invalid {conf_field} type for {filename}"
        assert 0 <= conf_value <= 100, f"{conf_field} out of range for {filename}: {conf_value}"
    
    # Validate V2-compatibility fields
    assert 'ocr_engine' in result, f"Missing 'ocr_engine' field for {filename}"
    assert 'ocr_confidence' in result, f"Missing 'ocr_confidence' field for {filename}"
    
    return True


def run_integration_tests(quick: bool = False, verbose: bool = False) -> int:
    """
    Run integration tests against all receipt images.
    
    Args:
        quick: If True, only test first 2 images
        verbose: If True, show raw model responses
    """
    print("\n" + "="*100)
    print("RECEIPT ANALYZER V3 - INTEGRATION TESTS (Ollama Vision LLM)")
    print("="*100)

    # Initialize analyzer
    print("\n[INFO] Initializing ReceiptAnalyzerV3...")
    analyzer = ReceiptAnalyzerV3()
    
    # Check Ollama connection FIRST - fail hard if not available
    print("\n[INFO] Checking Ollama connection...")
    if not analyzer.check_ollama_connection():
        print("\n" + "!"*100)
        print("FATAL ERROR: Cannot connect to Ollama or model not available!")
        print("Make sure Ollama is running and the model is pulled:")
        print(f"  ollama pull {analyzer.model}")
        print("!"*100)
        sys.exit(1)
    
    print("[INFO] Ollama connection OK ✓")
    
    # Find receipt images
    receipts_dir = 'data/receipts'
    if not os.path.exists(receipts_dir):
        print(f"\n[ERROR] Receipts directory not found: {receipts_dir}")
        sys.exit(1)
    
    receipt_files = sorted([f for f in os.listdir(receipts_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    
    if not receipt_files:
        print(f"\n[ERROR] No receipt images found in {receipts_dir}")
        sys.exit(1)
    
    if quick:
        receipt_files = receipt_files[:2]
        print(f"\n[INFO] Quick mode: testing only first {len(receipt_files)} images")
    else:
        print(f"\n[INFO] Found {len(receipt_files)} receipt images to test")
    
    # Expected results (for reference, not strict matching)
    expected_data = {
        'receipt_20260109_155213.jpg': {'expected_amount_range': (150, 160), 'expected_category': 'Compras'},
        'receipt_20260109_155314.jpg': {'expected_amount_range': (3, 4), 'expected_category': 'Compras'},
        'receipt_20260109_191356.jpg': {'expected_amount_range': (35, 40), 'expected_category': 'Comida'},
        'receipt_20260109_191458.jpg': {'expected_amount_range': (35, 40), 'expected_category': 'Comida'},
        'receipt_20260109_191624.jpg': {'expected_amount_range': (35, 40), 'expected_category': 'Comida'},
        'receipt_20260109_215746.jpg': {'expected_amount_range': (28, 32), 'expected_category': 'Comida'},
    }
    
    # Run tests
    print_separator()
    print("RUNNING TESTS")
    print_separator()
    
    results = []
    passed = 0
    failed = 0
    
    for idx, filename in enumerate(receipt_files, 1):
        filepath = os.path.join(receipts_dir, filename)
        expected = expected_data.get(filename, {})
        
        print(f"\n[TEST {idx}/{len(receipt_files)}] {filename}")
        print_separator('-', 100)
        
        try:
            # Analyze receipt - this will raise on Ollama/JSON errors
            result = analyzer.analyze_receipt(filepath)
            
            # Print result details
            print_result_detail(result, verbose)
            
            # Validate result - this will raise AssertionError on validation failures
            validate_result(result, filename)
            
            # Check against expected values (warnings only, not failures)
            if expected:
                if result and 'expected_amount_range' in expected:
                    min_amt, max_amt = expected['expected_amount_range']
                    if not (min_amt <= result['amount'] <= max_amt):
                        print(f"  ⚠️  Amount {result['amount']} outside expected range ({min_amt}-{max_amt})")

                if result and 'expected_category' in expected:
                    if result['category'] != expected['expected_category']:
                        print(f"  ⚠️  Category '{result['category']}' differs from expected '{expected['expected_category']}'")
            
            print(f"\n  ✅ PASSED - All validations OK")
            passed += 1
            results.append({'filename': filename, 'status': 'PASSED', 'result': result})
            
        except Exception as e:
            print(f"\n  ❌ FAILED: {type(e).__name__}: {e}")
            failed += 1
            results.append({'filename': filename, 'status': 'FAILED', 'error': str(e)})
            
            # In strict test mode, we fail hard on any error
            if not os.getenv('TEST_CONTINUE_ON_ERROR', ''):
                print("\n" + "!"*100)
                print(f"TEST FAILED HARD on {filename}")
                print(f"Error: {e}")
                print("Set TEST_CONTINUE_ON_ERROR=1 to continue after failures")
                print("!"*100)
                sys.exit(1)
    
    # Summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    print(f"\n  Total tests: {len(receipt_files)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print(f"\n  🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n  💥 {failed} TEST(S) FAILED")
        return 1


def run_unit_tests() -> int:
    """
    Run unit tests for JSON parsing and validation (no Ollama required).
    """
    print("\n" + "="*100)
    print("RECEIPT ANALYZER V3 - UNIT TESTS (Parser/Validator)")
    print("="*100)
    
    from receipt_analyzer_v3 import ReceiptAnalyzerV3
    
    analyzer = ReceiptAnalyzerV3()
    
    # Test JSON parsing
    test_cases = [
        # Valid JSON
        {
            'input': '{"amount": 37.79, "date": "2026-01-09", "title": "ALDI", "category": "Comida", "confidence": 85}',
            'should_pass': True,
            'expected_amount': 37.79,
            'expected_category': 'Comida'
        },
        # JSON with markdown code block
        {
            'input': '```json\n{"amount": 10.50, "date": "2025-12-01", "title": "Test", "category": "Otros", "confidence": 70}\n```',
            'should_pass': True,
            'expected_amount': 10.50,
            'expected_category': 'Otros'
        },
        # Invalid category (should fail validation)
        {
            'input': '{"amount": 20.00, "date": "2025-01-01", "title": "Test", "category": "InvalidCat", "confidence": 50}',
            'should_pass': True,  # Parser passes, but category gets normalized to 'Otros'
            'expected_category': 'Otros'
        },
        # Missing field (should fail)
        {
            'input': '{"amount": 20.00, "title": "Test", "category": "Comida", "confidence": 50}',
            'should_pass': False
        },
        # Invalid JSON (should fail)
        {
            'input': 'This is not JSON at all',
            'should_pass': False
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\n[UNIT TEST {i}] ", end='')
        
        try:
            parsed = analyzer._parse_json_response(tc['input'])
            normalized = analyzer._validate_and_normalize(parsed)
            
            if not tc['should_pass']:
                print(f"❌ FAILED - Should have raised exception")
                failed += 1
                continue
            
            # Check expected values
            if 'expected_amount' in tc:
                assert normalized['amount'] == tc['expected_amount'], \
                    f"Amount mismatch: {normalized['amount']} != {tc['expected_amount']}"
            
            if 'expected_category' in tc:
                assert normalized['category'] == tc['expected_category'], \
                    f"Category mismatch: {normalized['category']} != {tc['expected_category']}"
            
            print(f"✅ PASSED")
            passed += 1
            
        except Exception as e:
            if tc['should_pass']:
                print(f"❌ FAILED - {type(e).__name__}: {e}")
                failed += 1
            else:
                print(f"✅ PASSED (correctly raised {type(e).__name__})")
                passed += 1
    
    print("\n" + "-"*100)
    print(f"Unit tests: {passed} passed, {failed} failed")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test ReceiptAnalyzerV3')
    parser.add_argument('--quick', action='store_true', help='Test only first 2 images')
    parser.add_argument('--verbose', action='store_true', help='Show raw model responses')
    parser.add_argument('--unit-only', action='store_true', help='Run only unit tests (no Ollama required)')
    parser.add_argument('--all', action='store_true', help='Run both unit and integration tests')
    
    args = parser.parse_args()
    
    exit_code = 0
    
    if args.unit_only:
        exit_code = run_unit_tests()
    elif args.all:
        exit_code = run_unit_tests()
        if exit_code == 0:
            exit_code = run_integration_tests(quick=args.quick, verbose=args.verbose)
    else:
        exit_code = run_integration_tests(quick=args.quick, verbose=args.verbose)
    
    sys.exit(exit_code)
