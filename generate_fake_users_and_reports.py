"""
Generate fake users and their reports directly to database.
Creates 10 users + 20 weeks of data for each.
Run: python generate_fake_users_and_reports.py
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Database
from services.reports import ReportService
from utils.date_utils import jalali_to_gregorian

# 10 fake users
users_data = [
    {"full_name": "امیرحسین غدیمی", "phone": "09123456701"},
    {"full_name": "سارا احمدی", "phone": "09123456702"},
    {"full_name": "محمد رضایی", "phone": "09123456703"},
    {"full_name": "فاطمه محمدی", "phone": "09123456704"},
    {"full_name": "علی کریمی", "phone": "09123456705"},
    {"full_name": "مریم حسینی", "phone": "09123456706"},
    {"full_name": "حسن نوری", "phone": "09123456707"},
    {"full_name": "نرگس سلطانی", "phone": "09123456708"},
    {"full_name": "رضا مظاهری", "phone": "09123456709"},
    {"full_name": "زهرا کاظمی", "phone": "09123456710"},
]

def create_fake_data():
    db = Database()
    report_service = ReportService(db)
    
    print("Creating fake users and reports...")
    print("="*60)
    
    # Create users
    user_ids = []
    for i, user_info in enumerate(users_data, 1):
        # Check if user exists
        existing = None
        for u in db.get_all_users():
            if u.full_name == user_info["full_name"]:
                existing = u
                break
        
        if existing:
            user_id = existing.id
            print(f"  {i}. {user_info['full_name']} - already exists (ID: {user_id})")
        else:
            # Create user with fake bale_id
            from models.models import User
            user = User(
                bale_id=100000000 + i,  # Fake Bale ID
                full_name=user_info["full_name"],
                phone=user_info["phone"]
            )
            user_id = db.add_user(user)
            print(f"  {i}. {user_info['full_name']} - created (ID: {user_id})")
        
        user_ids.append(user_id)
    
    print("\nGenerating 20 weeks of reports...")
    print("="*60)
    
    # Base date: 20 weeks ago (around 1403/11/01)
    base_date = datetime(2025, 1, 15).date()  # Around 1403/11/01
    
    total_reports = 0
    
    for week in range(1, 21):  # Weeks 1-20
        week_start = base_date + timedelta(weeks=week-1)
        
        # Generate 5 days of reports per week (Saturday to Wednesday)
        for day in range(5):
            report_date = week_start + timedelta(days=day)
            
            # Skip if in future
            if report_date > datetime.now().date():
                continue
            
            for user_id in user_ids:
                # 80% chance of having a report (not everyone reports every day)
                if random.random() > 0.2:
                    # Random hours with realistic patterns
                    # Some users work more consistently
                    main_hours = round(random.uniform(4, 9), 1)
                    side_hours = round(random.uniform(0, 5), 1)
                    
                    # Occasionally high/low days
                    if random.random() > 0.9:  # 10% chance of high day
                        main_hours = round(random.uniform(10, 12), 1)
                    elif random.random() > 0.9:  # 10% chance of low day
                        main_hours = round(random.uniform(1, 3), 1)
                    
                    try:
                        success, _ = report_service.submit_daily_report(
                            user_id=user_id,
                            main_hours=main_hours,
                            side_hours=side_hours,
                            report_date=report_date
                        )
                        if success:
                            total_reports += 1
                    except Exception as e:
                        # Report might already exist
                        pass
        
        if week % 5 == 0:
            print(f"  Week {week}/20 completed... ({total_reports} reports so far)")
    
    print("\n" + "="*60)
    print(f"✅ Done!")
    print(f"   Users created: {len(user_ids)}")
    print(f"   Total reports: {total_reports}")
    print(f"   Date range: {base_date} to {base_date + timedelta(weeks=20)}")
    print(f"\nNow check the dashboard:")
    print(f"   python dashboard/app.py")
    print(f"   http://localhost:5000/analytics")

if __name__ == "__main__":
    create_fake_data()
