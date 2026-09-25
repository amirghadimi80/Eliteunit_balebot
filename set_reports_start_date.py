"""
Set the first required report day for an existing user.

Usage:
  python set_reports_start_date.py --name "نام کامل" --date 2026-03-20
  python set_reports_start_date.py --id 12 --date 2026-03-20
  python set_reports_start_date.py --id 12 --clear
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Database


def main():
    parser = argparse.ArgumentParser(
        description="Set reports_start_date for a user (YYYY-MM-DD)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, help="User database ID")
    group.add_argument("--name", type=str, help="User full name (exact match)")
    parser.add_argument(
        "--date",
        type=str,
        help="Start date YYYY-MM-DD (first day they must report)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear explicit start date (fall back to created_at)",
    )
    args = parser.parse_args()

    if not args.clear and not args.date:
        parser.error("Provide --date YYYY-MM-DD or --clear")

    db = Database()

    if args.id is not None:
        user = db.get_user_by_id(args.id)
    else:
        user = db.get_user_by_full_name(args.name)

    if not user:
        print("❌ کاربر پیدا نشد.")
        sys.exit(1)

    start_value = None if args.clear else args.date.strip()
    if not db.set_user_reports_start_date(user.id, start_value):
        print("❌ ذخیره نشد (تاریخ نامعتبر؟).")
        sys.exit(1)

    effective = db.get_user_reports_start_date(db.get_user_by_id(user.id))
    print(f"✅ {user.full_name} (id={user.id})")
    print(f"   reports_start_date = {start_value!r}")
    print(f"   effective start    = {effective}")


if __name__ == "__main__":
    main()
