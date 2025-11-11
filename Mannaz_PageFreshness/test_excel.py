"""
Test Excel Report Generation
Quick test to verify Excel generation works
"""

import pandas as pd
from datetime import datetime
import os

print("=" * 70)
print("TESTING EXCEL REPORT GENERATION")
print("=" * 70)

# Test 1: Check imports
print("\n[1] Testing imports...")
try:
    from generate_excel_report import create_excel_report
    print("  ✓ generate_excel_report.py imported successfully")
except ImportError as e:
    print(f"  ❌ Cannot import generate_excel_report.py: {e}")
    print(f"  Current directory: {os.getcwd()}")
    print(f"  Files in directory: {os.listdir('.')}")
    input("\nPress Enter to exit...")
    exit(1)

# Test 2: Create sample data
print("\n[2] Creating sample data...")
current_data = {
    'url': [
        'https://www.mannaz.com/da/artikler/test1',
        'https://www.mannaz.com/da/artikler/test2',
        'https://www.mannaz.com/da/artikler/test3',
        'https://www.mannaz.com/da/artikler/test4',
        'https://www.mannaz.com/da/artikler/test5',
    ],
    'path': ['/da/artikler/test1', '/da/artikler/test2', '/da/artikler/test3', '/da/artikler/test4', '/da/artikler/test5'],
    'language': ['DA', 'DA', 'DA', 'EN', 'EN'],
    'title': ['Test Article 1', 'Test Article 2', 'Test Article 3', 'Test Article 4', 'Test Article 5'],
    'tags': ['Leadership', 'Management', 'Strategy', 'Innovation', 'Leadership'],
    'date_created': ['2024-01-15', '2024-02-20', '2023-12-10', '2024-03-05', '2023-06-15'],
    'date_modified': ['2024-11-20', '2024-10-15', '2024-01-10', '2024-11-25', '2024-01-20'],
    'freshness': ['Fresh', 'Rotting', 'Outdated', 'Fresh', 'Outdated'],
    'scraped_at': ['2025-01-15', '2025-01-15', '2025-01-15', '2025-01-15', '2025-01-15']
}

current_df = pd.DataFrame(current_data)
print(f"  ✓ Created current_df with {len(current_df)} rows")

# Create previous month data
previous_data = {
    'url': [
        'https://www.mannaz.com/da/artikler/test1',
        'https://www.mannaz.com/da/artikler/test2',
        'https://www.mannaz.com/da/artikler/test3',
    ],
    'path': ['/da/artikler/test1', '/da/artikler/test2', '/da/artikler/test3'],
    'language': ['DA', 'DA', 'DA'],
    'title': ['Test Article 1', 'Test Article 2', 'Test Article 3'],
    'date_modified': ['2024-10-20', '2024-10-15', '2024-01-10'],
    'freshness': ['Rotting', 'Fresh', 'Rotting'],
}

previous_df = pd.DataFrame(previous_data)
print(f"  ✓ Created previous_df with {len(previous_df)} rows")

# Create changes data
changes_data = {
    'url': ['https://www.mannaz.com/da/artikler/test1', 'https://www.mannaz.com/da/artikler/test2'],
    'path': ['/da/artikler/test1', '/da/artikler/test2'],
    'title': ['Test Article 1', 'Test Article 2'],
    'status_change': ['Rotting → Fresh ✅', 'Fresh → Rotting ⚠️'],
    'freshness_previous': ['Rotting', 'Fresh'],
    'freshness_current': ['Fresh', 'Rotting'],
    'date_modified': ['2024-11-20', '2024-10-15']
}

changes_df = pd.DataFrame(changes_data)
print(f"  ✓ Created changes_df with {len(changes_df)} rows")

# Test 3: Set output path
print("\n[3] Setting output path...")
output_file = os.path.join(os.getcwd(), "TEST_Excel_Report.xlsx")
print(f"  Output file: {output_file}")

# Test 4: Generate Excel
print("\n[4] Generating Excel report...")
try:
    create_excel_report(current_df, previous_df, changes_df, output_file)
    print(f"  ✓ Excel report created successfully")
except Exception as e:
    print(f"  ❌ Error creating Excel: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    exit(1)

# Test 5: Check file exists
print("\n[5] Verifying file...")
if os.path.exists(output_file):
    file_size = os.path.getsize(output_file)
    print(f"  ✓ File exists: {output_file}")
    print(f"  File size: {file_size:,} bytes")
else:
    print(f"  ❌ File not found: {output_file}")
    input("\nPress Enter to exit...")
    exit(1)

# Test 6: Try to open
print("\n[6] Opening Excel file...")
try:
    import platform
    if platform.system() == 'Windows':
        os.startfile(output_file)
        print("  ✓ Excel file opened")
    else:
        print(f"  Manual open required: {output_file}")
except Exception as e:
    print(f"  ⚠️  Could not open automatically: {e}")
    print(f"  Manually open: {output_file}")

print("\n" + "=" * 70)
print("TEST COMPLETE!")
print("=" * 70)
print("\nCheck the Excel file has these sheets:")
print("  1. Dashboard (with charts)")
print("  2. Updated Articles")
print("  3. Status Changes")
print("  4. All Pages")
print("\nIf all sheets exist, the system is working correctly!")

input("\nPress Enter to exit...")
