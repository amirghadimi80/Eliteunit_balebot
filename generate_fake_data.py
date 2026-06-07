"""
Generate fake sample data for testing charts.
Creates 10 users with 20 weeks of random reports.
Run: python generate_fake_data.py
"""

import pandas as pd
import random
from datetime import datetime, timedelta

# 10 fake users with Persian names
users = [
    "امیرحسین غدیمی",
    "سارا احمدی",
    "محمد رضایی",
    "فاطمه محمدی",
    "علی کریمی",
    "مریم حسینی",
    "حسن نوری",
    "نرگس سلطانی",
    "رضا مظاهری",
    "زهرا کاظمی"
]

# Generate data for 20 weeks
# Starting from week 1 (about 5 months ago)
data = []

# Base date: 20 weeks ago
base_date = datetime(2025, 1, 1)  # Around Ordibehesht 1404

for week in range(1, 21):  # Weeks 1-20
    for user in users:
        # Random hours with some realistic variation
        # Some users work more, some less
        base_main = random.uniform(20, 45)  # Main hours per week
        base_side = random.uniform(5, 20)   # Side hours per week
        
        # Add some variation per week
        main_hours = round(base_main + random.uniform(-10, 10), 1)
        side_hours = round(base_side + random.uniform(-5, 5), 1)
        
        # Ensure non-negative
        main_hours = max(0, main_hours)
        side_hours = max(0, side_hours)
        
        # Calculate date for this week (weeks 1-20)
        week_date = base_date + timedelta(weeks=week-1)
        
        # Convert to Jalali (approximate for demo)
        # Week 1 = around 1403/11/01 (late winter)
        # Adding weeks progressively
        jalali_month = 11 + (week // 4)
        jalali_day = (week % 4) * 7 + 1
        if jalali_month > 12:
            jalali_month = jalali_month - 12
            year = 1404
        else:
            year = 1403
        
        date_shamsi = f"{year}/{jalali_month:02d}/{jalali_day:02d}"
        
        data.append({
            'name': user,
            'date_shamsi': date_shamsi,
            'main_hours': main_hours,
            'side_hours': side_hours,
            'week': week
        })

# Create DataFrame and save
df = pd.DataFrame(data)
df.to_excel('sample_data_20weeks.xlsx', index=False)

print("✅ Fake data generated: sample_data_20weeks.xlsx")
print(f"   Users: {len(users)}")
print(f"   Weeks: 20")
print(f"   Total records: {len(data)}")
print(f"\nTo import, run:")
print(f"   python import_reports.py sample_data_20weeks.xlsx")
print(f"\nNote: Users must exist in database first!")
print(f"Run: python bot.py (then /start in Bale to register users)")
