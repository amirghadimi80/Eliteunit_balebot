"""
Database initialization and management module for SQLite.
Handles all database operations including user, report, and penalty records.
"""

import sqlite3
import logging
from typing import Optional, List, Tuple
from datetime import date, datetime
from pathlib import Path

from config.settings import DATABASE_PATH, DATABASE_SCHEMA
from models.models import User, Report, Penalty
from utils.date_utils import get_today_gregorian

# Setup logging
logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for EliteUniteTime system."""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create all tables
            for table_name, schema in DATABASE_SCHEMA.items():
                cursor.execute(schema)
                logger.info(f"Table '{table_name}' initialized successfully")
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    # =====================
    # USER OPERATIONS
    # =====================
    
    def user_exists(self, bale_id: int) -> bool:
        """
        Check if user exists by bale_id.
        
        Args:
            bale_id: Bale user ID
            
        Returns:
            bool: True if user exists
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE bale_id = ?", (bale_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking user existence: {e}")
            return False
    
    def add_user(self, user: User) -> Optional[int]:
        """
        Add a new user to database.
        
        Args:
            user: User object to add
            
        Returns:
            Optional[int]: User ID if successful, None otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (bale_id, full_name, phone, bio)
                   VALUES (?, ?, ?, ?)""",
                (user.bale_id, user.full_name, user.phone or "", user.bio or "")
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            logger.info(f"User added: {user.full_name} (ID: {user_id})")
            return user_id
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    @staticmethod
    def _row_to_user(row) -> "User":
        """Convert a sqlite3.Row to a User object safely."""
        d = dict(row)
        return User(
            id=d.get("id"),
            bale_id=d.get("bale_id"),
            full_name=d.get("full_name", ""),
            phone=d.get("phone", ""),
            bio=d.get("bio", ""),
            interests=d.get("interests", ""),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )

    def get_user_by_bale_id(self, bale_id: int) -> Optional[User]:
        """
        Get user by Bale ID.
        
        Args:
            bale_id: Bale user ID
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE bale_id = ?",
                (bale_id,)
            )
            row = cursor.fetchone()
            conn.close()
            return self._row_to_user(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User object if found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            return self._row_to_user(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_all_users(self) -> List[User]:
        """
        Get all users from database.
        
        Returns:
            List[User]: List of all users
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            return [self._row_to_user(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def update_user(self, user: User) -> bool:
        """
        Update user information.
        
        Args:
            user: User object with updated data
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users 
                   SET full_name = ?, phone = ?, bio = ?, interests = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (user.full_name, user.phone, user.bio, user.interests, user.id)
            )
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    # =====================
    # REPORT OPERATIONS
    # =====================
    
    def report_exists(self, user_id: int, date_gregorian: str) -> bool:
        """
        Check if report exists for a user on a specific date.
        
        Args:
            user_id: User ID
            date_gregorian: Date in format YYYY-MM-DD
            
        Returns:
            bool: True if report exists
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM reports WHERE user_id = ? AND date_gregorian = ?",
                (user_id, date_gregorian)
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking report existence: {e}")
            return False
    
    def add_report(self, report: Report) -> Optional[int]:
        """
        Add a new report.
        
        Args:
            report: Report object to add
            
        Returns:
            Optional[int]: Report ID if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO reports 
                   (user_id, date_shamsi, date_gregorian, main_hours, side_hours, total_hours)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    report.user_id,
                    report.date_shamsi,
                    report.date_gregorian,
                    report.main_hours,
                    report.side_hours,
                    report.total_hours,
                )
            )
            conn.commit()
            report_id = cursor.lastrowid
            conn.close()
            logger.info(f"Report added: user_id={report.user_id}, date={report.date_shamsi}")
            return report_id
        except sqlite3.Error as e:
            logger.error(f"Error adding report: {e}")
            return None
    
    def get_report_by_id(self, report_id: int) -> Optional[Report]:
        """
        Get report by ID.
        
        Args:
            report_id: Report ID
            
        Returns:
            Optional[Report]: Report object if found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Report(
                    id=row["id"],
                    user_id=row["user_id"],
                    date_shamsi=row["date_shamsi"],
                    date_gregorian=row["date_gregorian"],
                    main_hours=row["main_hours"],
                    side_hours=row["side_hours"],
                    total_hours=row["total_hours"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting report: {e}")
            return None
    
    def get_reports_by_user_and_date(
        self,
        user_id: int,
        start_date: str,
        end_date: str
    ) -> List[Report]:
        """
        Get reports for a user within a date range.
        
        Args:
            user_id: User ID
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD
            
        Returns:
            List[Report]: List of reports
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM reports 
                   WHERE user_id = ? AND date_gregorian BETWEEN ? AND ?
                   ORDER BY date_gregorian DESC""",
                (user_id, start_date, end_date)
            )
            rows = cursor.fetchall()
            conn.close()
            
            reports = []
            for row in rows:
                report = Report(
                    id=row["id"],
                    user_id=row["user_id"],
                    date_shamsi=row["date_shamsi"],
                    date_gregorian=row["date_gregorian"],
                    main_hours=row["main_hours"],
                    side_hours=row["side_hours"],
                    total_hours=row["total_hours"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                reports.append(report)
            return reports
        except sqlite3.Error as e:
            logger.error(f"Error getting reports: {e}")
            return []
    
    def get_reports_by_date(self, date_gregorian: str) -> List[Report]:
        """
        Get all reports for a specific date.
        
        Args:
            date_gregorian: Date in format YYYY-MM-DD
            
        Returns:
            List[Report]: List of reports for that date
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM reports WHERE date_gregorian = ? ORDER BY created_at DESC",
                (date_gregorian,)
            )
            rows = cursor.fetchall()
            conn.close()
            
            reports = []
            for row in rows:
                report = Report(
                    id=row["id"],
                    user_id=row["user_id"],
                    date_shamsi=row["date_shamsi"],
                    date_gregorian=row["date_gregorian"],
                    main_hours=row["main_hours"],
                    side_hours=row["side_hours"],
                    total_hours=row["total_hours"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                reports.append(report)
            return reports
        except sqlite3.Error as e:
            logger.error(f"Error getting reports by date: {e}")
            return []
    
    # =====================
    # PENALTY OPERATIONS
    # =====================
    
    def add_penalty(self, penalty: Penalty) -> Optional[int]:
        """
        Add a new penalty record.
        
        Args:
            penalty: Penalty object to add
            
        Returns:
            Optional[int]: Penalty ID if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO penalties 
                   (user_id, date_shamsi, date_gregorian, amount, reason, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    penalty.user_id,
                    penalty.date_shamsi,
                    penalty.date_gregorian,
                    penalty.amount,
                    penalty.reason,
                    penalty.status,
                )
            )
            conn.commit()
            penalty_id = cursor.lastrowid
            conn.close()
            logger.info(f"Penalty added: user_id={penalty.user_id}, reason={penalty.reason}")
            return penalty_id
        except sqlite3.Error as e:
            logger.error(f"Error adding penalty: {e}")
            return None
    
    def get_penalties_by_user(self, user_id: int, status: Optional[str] = None) -> List[Penalty]:
        """
        Get penalties for a user.
        
        Args:
            user_id: User ID
            status: Filter by status (paid/unpaid), None for all
            
        Returns:
            List[Penalty]: List of penalties
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    "SELECT * FROM penalties WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, status)
                )
            else:
                cursor.execute(
                    "SELECT * FROM penalties WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
            
            rows = cursor.fetchall()
            conn.close()
            
            penalties = []
            for row in rows:
                penalty = Penalty(
                    id=row["id"],
                    user_id=row["user_id"],
                    date_shamsi=row["date_shamsi"],
                    date_gregorian=row["date_gregorian"],
                    amount=row["amount"],
                    reason=row["reason"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
                penalties.append(penalty)
            return penalties
        except sqlite3.Error as e:
            logger.error(f"Error getting penalties: {e}")
            return []
    
    def mark_penalty_paid(self, penalty_id: int) -> bool:
        """
        Mark a penalty as paid.
        
        Args:
            penalty_id: Penalty ID
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE penalties SET status = 'paid' WHERE id = ?",
                (penalty_id,)
            )
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error marking penalty as paid: {e}")
            return False
    
    def get_missing_report_users(self, date_gregorian: str) -> List[Tuple[int, str]]:
        """
        Get users who haven't reported for a specific date.
        
        Args:
            date_gregorian: Date in format YYYY-MM-DD
            
        Returns:
            List[Tuple[int, str]]: List of (user_id, full_name) tuples
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT u.id, u.full_name FROM users u
                   WHERE u.id NOT IN (
                       SELECT user_id FROM reports WHERE date_gregorian = ?
                   )
                   ORDER BY u.full_name""",
                (date_gregorian,)
            )
            results = cursor.fetchall()
            conn.close()
            return [(row["id"], row["full_name"]) for row in results]
        except sqlite3.Error as e:
            logger.error(f"Error getting missing report users: {e}")
            return []

    # =====================
    # DELETE OPERATIONS (Admin only)
    # =====================
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user and all related data (reports, penalties).
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete related penalties
            cursor.execute("DELETE FROM penalties WHERE user_id = ?", (user_id,))
            # Delete related reports
            cursor.execute("DELETE FROM reports WHERE user_id = ?", (user_id,))
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} and all related data deleted")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def delete_report(self, report_id: int) -> bool:
        """
        Delete a specific report.
        
        Args:
            report_id: Report ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            conn.commit()
            conn.close()
            logger.info(f"Report {report_id} deleted")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting report: {e}")
            return False
    
    def delete_penalty(self, penalty_id: int) -> bool:
        """
        Delete a specific penalty.
        
        Args:
            penalty_id: Penalty ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM penalties WHERE id = ?", (penalty_id,))
            conn.commit()
            conn.close()
            logger.info(f"Penalty {penalty_id} deleted")
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting penalty: {e}")
            return False
