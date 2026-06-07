"""
Clear fake data from database.
Remove all fake users and their reports.
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Database

# Fake users to remove
FAKE_USERS = [
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

def clear_fake_data():
    db = Database()
    
    print("Checking for fake users...")
    print("="*60)
    
    users_to_delete = []
    for user in db.get_all_users():
        if user.full_name in FAKE_USERS:
            users_to_delete.append(user)
            print(f"  Found fake user: {user.full_name} (ID: {user.id})")
    
    if not users_to_delete:
        print("  No fake users found.")
        return
    
    print(f"\nDeleting {len(users_to_delete)} fake users and their reports...")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    deleted_count = 0
    for user in users_to_delete:
        # Delete reports first (foreign key)
        cursor.execute("DELETE FROM reports WHERE user_id = ?", (user.id,))
        reports_deleted = cursor.rowcount
        
        # Delete penalties
        cursor.execute("DELETE FROM penalties WHERE user_id = ?", (user.id,))
        penalties_deleted = cursor.rowcount
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user.id,))
        
        print(f"  Deleted: {user.full_name} ({reports_deleted} reports, {penalties_deleted} penalties)")
        deleted_count += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print(f"✅ Deleted {deleted_count} fake users")
    print("="*60)

if __name__ == "__main__":
    clear_fake_data()
