"""
Reset all penalties — keeps users and reports intact.
Use when starting fresh with the penalty system.
"""

import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from database.db import Database


def reset_penalties() -> None:
    db = Database()
    deleted = db.delete_all_penalties()
    print(f"✅ {deleted} جریمه حذف شد. گزارش‌ها و کاربران بدون تغییر ماندند.")


if __name__ == "__main__":
    reset_penalties()
