#!/usr/bin/env python3
"""Test subsidiary mapping logic"""

# Mapping configuration (from ingestion script)
PRACTICE_MAPPING = {
    'eastlake': {
        'name': 'Eastlake Dental',
        'location': 'Seattle, WA',
        'subsidiary_patterns': [
            'SCDP Eastlake',
            'Eastlake'
        ]
    },
    'torrey_pines': {
        'name': 'Torrey Pines Dental',
        'location': 'San Diego, CA',
        'subsidiary_patterns': [
            'SCDP Torrey Pines',
            'Torrey Pines',
            'Torrey Highlands'
        ]
    },
    'ads': {
        'name': 'Advanced Dental Solutions',
        'location': 'San Diego, CA',
        'subsidiary_patterns': [
            'SCDP San Marcos',
            'San Marcos',
            'Mission Hills'
        ]
    }
}

DEFAULT_PRACTICE = 'eastlake'

def map_subsidiary_to_practice(subsidiary_text: str) -> str:
    """Map NetSuite subsidiary hierarchy to practice tenant_id"""
    if not subsidiary_text:
        return DEFAULT_PRACTICE

    for practice_id, practice_info in PRACTICE_MAPPING.items():
        for pattern in practice_info['subsidiary_patterns']:
            if pattern.lower() in subsidiary_text.lower():
                return practice_id

    return DEFAULT_PRACTICE

# Test cases
test_cases = [
    ('Parent Company : Silver Creek Dental Partners, LLC : SCDP Holdings, LLC : SCDP Torrey Pines, LLC', 'torrey_pines'),
    ('Parent Company : Silver Creek Dental Partners, LLC : SCDP Holdings, LLC : SCDP San Marcos, LLC', 'ads'),
    ('Parent Company : Silver Creek Dental Partners, LLC : SCDP Holdings, LLC : SCDP San Marcos II, LLC', 'ads'),
    ('Parent Company : Silver Creek Dental Partners, LLC : SCDP Holdings, LLC : SCDP Eastlake, LLC', 'eastlake'),
    ('Parent Company : Silver Creek Dental Partners, LLC : SCDP Holdings, LLC : SCDP Torrey Highlands, LLC', 'torrey_pines'),
    ('Parent Company : Silver Creek Dental Partners, LLC', 'eastlake'),  # default
    ('Parent Company', 'eastlake'),  # default
    ('', 'eastlake'),  # default
]

print('\n' + '='*80)
print('TESTING SUBSIDIARY MAPPING LOGIC')
print('='*80)

passed = 0
failed = 0

for subsidiary, expected in test_cases:
    result = map_subsidiary_to_practice(subsidiary)
    status = '✓ PASS' if result == expected else '✗ FAIL'

    if result == expected:
        passed += 1
    else:
        failed += 1

    print(f'\n{status}')
    print(f'  Input:    {subsidiary[:70]}')
    print(f'  Expected: {expected}')
    print(f'  Got:      {result}')

print('\n' + '='*80)
print(f'RESULTS: {passed} passed, {failed} failed')
print('='*80)
