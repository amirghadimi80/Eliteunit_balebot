"""
Create sample Excel template for importing reports.
Run: python import_template.py
"""

import pandas as pd

# Create sample data
data = {
    'name': ['نام کاربر 1', 'نام کاربر 2', 'نام کاربر 1'],
    'date_shamsi': ['1405/02/15', '1405/02/15', '1405/02/16'],
    'main_hours': [6.5, 8.0, 7.0],
    'side_hours': [2.0, 1.5, 3.0]
}

df = pd.DataFrame(data)
df.to_excel('import_template.xlsx', index=False)

print("✅ Template created: import_template.xlsx")
print("\nColumns:")
print("- name: Full name (must match user name in system)")
print("- date_shamsi: Persian date (1405/02/15)")
print("- main_hours: Main working hours (e.g., 6.5)")
print("- side_hours: Side working hours (e.g., 2.0)")
