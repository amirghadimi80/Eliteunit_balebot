"""
Import real data from ساعت.xlsx to database.
Creates users and imports their reports.
"""

import sys
import io
import pandas as pd
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Database
from services.reports import ReportService
from utils.date_utils import jalali_to_gregorian
from models.models import User

# Real users from the Excel file
REAL_USERS = [
    "علی کرباسی زاده",
    "محمدرضا عابدینی",
    "امیرحسین قدیمی",
    "یاسین عسگری",
    "سینا مرتضی",
    "محمد دهقانی",
    "امیرحسین قربانی",
    "مهران مرتضی",
    "علی حسنی پور",
    "مهدی صدیق",
    "محمد اصطهباناتی"
]

def import_real_data(excel_path: str):
    db = Database()
    report_service = ReportService(db)
    
    print("Reading Excel file...")
    df = pd.read_excel(excel_path)
    print(f"Total rows in Excel: {len(df)}")
    
    # Create users first
    print("\nCreating users...")
    print("="*60)
    
    user_id_map = {}  # Map name to user_id
    for i, name in enumerate(REAL_USERS, 1):
        # Check if user exists
        existing = None
        for u in db.get_all_users():
            if u.full_name == name:
                existing = u
                break
        
        if existing:
            user_id = existing.id
            print(f"  {i}. {name} - already exists (ID: {user_id})")
        else:
            # Create user with fake bale_id
            user = User(
                bale_id=200000000 + i,  # Fake Bale ID for real users
                full_name=name,
                phone=f"091211111{i:02d}"
            )
            user_id = db.add_user(user)
            print(f"  {i}. {name} - created (ID: {user_id})")
        
        user_id_map[name] = user_id
    
    print("\nImporting reports...")
    print("="*60)
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for _, row in df.iterrows():
        try:
            name = row.iloc[0]  # First column is name
            date_str = row.iloc[1]  # Second column is date
            col1 = row.iloc[2]  # Third column (main or total)
            col2 = row.iloc[3]  # Fourth column (side or NaN)
            
            # Find user
            if name not in user_id_map:
                print(f"  ⚠️ User not found: {name}")
                error_count += 1
                continue
            
            user_id = user_id_map[name]
            
            # Parse date (format: 1404-11-15)
            parts = str(date_str).split('-')
            if len(parts) != 3:
                print(f"  ⚠️ Invalid date format: {date_str}")
                error_count += 1
                continue
            
            j_year, j_month, j_day = int(parts[0]), int(parts[1]), int(parts[2])
            
            # Convert to Gregorian
            try:
                g_date = jalali_to_gregorian(j_year, j_month, j_day)
            except:
                print(f"  ⚠️ Invalid date: {date_str}")
                error_count += 1
                continue
            
            # Determine main and side hours
            # If col2 is NaN, then col1 is total (treat as main)
            # If both have values, col1 is main, col2 is side
            if pd.isna(col2):
                main_hours = float(col1) if not pd.isna(col1) else 0.0
                side_hours = 0.0
            else:
                main_hours = float(col1) if not pd.isna(col1) else 0.0
                side_hours = float(col2) if not pd.isna(col2) else 0.0
            
            # Submit report
            success, message = report_service.submit_daily_report(
                user_id=user_id,
                main_hours=main_hours,
                side_hours=side_hours,
                report_date=g_date
            )
            
            if success:
                success_count += 1
                if success_count % 50 == 0:
                    print(f"  Progress: {success_count} reports imported...")
            else:
                if "already exists" in message:
                    skip_count += 1
                else:
                    print(f"  ⚠️ {name} - {date_str}: {message}")
                    error_count += 1
                
        except Exception as e:
            print(f"  ❌ Error processing row: {e}")
            error_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Successfully imported: {success_count}")
    print(f"⏭️  Skipped (duplicates): {skip_count}")
    print(f"⚠️  Errors: {error_count}")
    print(f"="*60)

if __name__ == "__main__":
    excel_file = r"c:\Users\afraa\Downloads\ساعت.xlsx"
    
    if not Path(excel_file).exists():
        print(f"❌ File not found: {excel_file}")
        sys.exit(1)
    
    import_real_data(excel_file)
