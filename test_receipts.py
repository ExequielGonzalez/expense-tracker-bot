#!/usr/bin/env python3
"""
Tests para validar el extractor de información de tickets
"""

from receipt_analyzer import ReceiptAnalyzer

def run_tests():
    analyzer = ReceiptAnalyzer()
    
    tests = [
        {
            'image': 'data/receipts/receipt_20260109_160649.jpg',
            'name': 'BOLOPTICA (sin fecha)',
            'expected_amount': 3.5,
            'expected_date': '1900-01-01',
            'expected_title': 'BOLOPTICA'
        },
        {
            'image': 'data/receipts/receipt_20260109_155213.jpg',
            'name': 'SOLOPTICAL (sin fecha)',
            'expected_amount': 154.0,
            'expected_date': '1900-01-01',
            'expected_title': 'SOLOPTICAL TORRE TRIANA'
        },
        {
            'image': 'data/receipts/receipt_20260109_155120.jpg',
            'name': 'GRUPO DIA',
            'expected_amount': 29.86,
            'expected_date': '2026-01-07',
            'expected_title': 'GRUPO DIA'
        }
    ]
    
    print('='*80)
    print('TESTS DE EXTRACCIÓN DE INFORMACIÓN DE TICKETS')
    print('='*80)
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\nTEST: {test['name']}")
        print(f"  Esperado: €{test['expected_amount']} | {test['expected_date']} | '{test['expected_title']}'")
        print('-' * 80)
        
        result = analyzer.analyze_receipt(test['image'])
        
        if result:
            amount_ok = result['amount'] == test['expected_amount']
            date_ok = result['date'] == test['expected_date']
            title_ok = result.get('title', '') == test['expected_title']
            
            amount_status = '✓' if amount_ok else '✗'
            date_status = '✓' if date_ok else '✗'
            title_status = '✓' if title_ok else '✗'
            
            print(f"  {amount_status} Monto extraído: {result['amount']}")
            print(f"  {date_status} Fecha extraída: {result['date']}")
            print(f"  {title_status} Título extraído: {result.get('title', 'N/A')}")
            
            if amount_ok and date_ok and title_ok:
                passed += 1
                print('  => TEST PASSED ✓')
            else:
                failed += 1
                print('  => TEST FAILED ✗')
        else:
            failed += 1
            print('  ✗ No se pudo extraer información')
            print('  => TEST FAILED ✗')
    
    print()
    print('='*80)
    print(f'RESULTADO FINAL: {passed}/{len(tests)} TESTS PASSED | {failed}/{len(tests)} TESTS FAILED')
    print('='*80)
    
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
