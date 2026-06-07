"""
Import historical reports from Excel/CSV to database.
Expected columns: name | date_shamsi | main_hours | side_hours
Example: امیرحسین غدیمی | 1405/02/15 | 6.5 | 2
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Database
from services.reports import ReportService
from utils.date_utils import jalali_to_gregorian

def import_from_excel(file_path: str):
    """Import reports from Excel file."""
    db = Database()
    report_service = ReportService(db)
    
    # Read Excel
    df = pd.read_excel(file_path)
    
    success_count = 0
    error_count = 0
    
    for _, row in df.iterrows():
        try:
            # Find user by name
            users = db.get_all_users()
            user = None
            for u in users:
                if u.full_name == row['name'] or row['name'] in u.full_name:
                    user = u
                    break
            
            if not user:
                print(f"⚠️ User not found: {row['name']}")
                error_count += 1
                continue
            
            # Convert Jalali to Gregorian
            parts = row['date_shamsi'].split('/')
            j_year, j_month, j_day = int(parts[0]), int(parts[1]), int(parts[2])
            g_date = jalali_to_gregorian(j_year, j_month, j_day)
            
            # Submit report
            success, message = report_service.submit_daily_report(
                user_id=user.id,
                main_hours=float(row['main_hours']),
                side_hours=float(row['side_hours']),
                report_date=g_date
            )
            
            if success:
                print(f"✅ {user.full_name} - {row['date_shamsi']}: {row['main_hours']} + {row['side_hours']}")
                success_count += 1
            else:
                print(f"⚠️ {user.full_name} - {row['date_shamsi']}: {message}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error processing row: {e}")
            error_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Successfully imported: {success_count}")
    print(f"⚠️ Errors: {error_count}")
    print(f"{'='*50}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_reports.py <excel_file.xlsx>")
        print("\nExcel format:")
        print("name | date_shamsi | main_hours | side_hours")
        print("امیرحسین غدیمی | 1405/02/15 | 6.5 | 2")
        sys.exit(1)
    
    import_from_excel(sys.argv[1])
