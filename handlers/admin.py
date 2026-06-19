"""
Admin panel handler for administrative functions.
"""

import logging
from io import BytesIO
import pandas as pd
from datetime import date
from balethon import Client
from balethon.objects import Message, InlineKeyboard, InlineKeyboardButton

from database.db import Database
from services.reports import ReportService
from services.penalty import PenaltyService
from config.settings import BALE_ADMIN_IDS
from utils.formatter import MessageFormatter

logger = logging.getLogger(__name__)


class AdminHandler:
    """Handler for administrative functions and reporting."""
    
    def __init__(self, db: Database):
        """
        Initialize admin handler.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.report_service = ReportService(db)
        self.penalty_service = PenaltyService(db)
    
    async def check_admin_permission(self, user_id: int) -> bool:
        """
        Check if user has admin privileges.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if user is admin
        """
        # Check against admin IDs or check if user is system admin
        user = self.db.get_user_by_bale_id(user_id)
        if not user:
            return False
        
        # Check if user_id is in BALE_ADMIN_IDS
        return user_id in BALE_ADMIN_IDS
    
    async def handle_admin_panel(self, client: Client, message: Message):
        """
        Show admin panel menu.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        # Check admin permission
        is_admin = await self.check_admin_permission(message.chat.id)
        
        if not is_admin:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ دسترسی غیرمجاز. این فقط برای ادمین‌ها است.",
            )
            return
        
        # Show admin menu
        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="👥 مشاهده تمام کاربران",
                callback_data="admin_view_users",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="📊 گزارش هفتگی",
                callback_data="admin_weekly_report",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="📈 دانلود Excel",
                callback_data="admin_export_excel",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="⚠️ مدیریت جریمه‌ها",
                callback_data="admin_penalties",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="🔄 بررسی دستی",
                callback_data="admin_manual_check",
            )
        )
        
        await client.send_message(
            chat_id=message.chat.id,
            text="⚙️ پنل ادمین:",
            reply_markup=keyboard,
        )
    
    async def handle_view_all_users(self, client: Client, message: Message):
        """
        Show list of all users.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        users = self.db.get_all_users()
        
        if not users:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ هیچ کاربری وجود ندارد.",
            )
            return
        
        # Format user list
        user_list = "👥 لیست کاربران:\n\n"
        for idx, user in enumerate(users, 1):
            user_list += f"{idx}. {user.full_name}"
            if user.phone:
                user_list += f" - {user.phone}"
            user_list += "\n"
        
        user_list += f"\n📊 کل کاربران: {len(users)}"
        
        await client.send_message(
            chat_id=message.chat.id,
            text=user_list,
        )
    
    async def handle_weekly_report_admin(self, client: Client, message: Message):
        """
        Generate and send weekly report for all users.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        stats_list = self.report_service.get_all_weekly_stats()
        
        if not stats_list:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ هیچ گزارشی وجود ندارد.",
            )
            return
        
        # Get first stats to extract week dates
        first_stats, _ = stats_list[0]
        
        # Format report
        summary_msg = MessageFormatter.format_admin_weekly_summary(
            first_stats.week_start,
            first_stats.week_end,
            [
                {
                    "user_name": name,
                    "main_hours": stats.main_hours,
                    "side_hours": stats.side_hours,
                    "total_hours": stats.total_hours,
                }
                for stats, name in stats_list
            ],
        )
        
        await client.send_message(
            chat_id=message.chat.id,
            text=summary_msg,
        )
    
    async def handle_export_excel(self, client: Client, message: Message):
        """
        Export weekly report as Excel file.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        try:
            stats_list = self.report_service.get_all_weekly_stats()
            
            if not stats_list:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="❌ هیچ داده‌ای برای صادرات وجود ندارد.",
                )
                return
            
            # Prepare data for Excel
            export_data = self.report_service.get_excel_export_data(stats_list)
            
            # Create DataFrame
            df = pd.DataFrame(export_data)
            
            # Create Excel file
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="گزارش", index=False)
            
            excel_buffer.seek(0)
            
            # Send file
            await client.send_document(
                chat_id=message.chat.id,
                document=excel_buffer,
                caption="📊 گزارش هفتگی - Excel",
            )
            
            logger.info("Excel export sent to admin")
        
        except Exception as e:
            logger.error(f"Error exporting Excel: {e}")
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ خطا در صادرات Excel: {str(e)}",
            )
    
    async def handle_penalties_management(self, client: Client, message: Message):
        """
        Show penalties management options.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        # Get summary of unpaid penalties
        summary = self.penalty_service.get_all_unpaid_penalties_summary()
        
        if not summary:
            await client.send_message(
                chat_id=message.chat.id,
                text="✅ تمام جریمه‌ها پرداخت شده‌اند.",
            )
            return
        
        # Format penalty summary
        penalty_msg = "⚠️ خلاصه جریمه‌ها:\n\n"
        for user_name, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
            penalty_msg += f"👤 {user_name}: {count:,} تومان\n"
        
        await client.send_message(
            chat_id=message.chat.id,
            text=penalty_msg,
        )
    
    async def handle_manual_penalty_check(self, client: Client, message: Message):
        """
        Manually trigger penalty check.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        # Import scheduler here to avoid circular imports
        from services.scheduler import SchedulerService
        
        try:
            # This would be called with the scheduler instance
            # For now, manually check
            from services.penalty import PenaltyService
            from utils.date_utils import get_yesterday, gregorian_to_jalali_str
            
            penalty_service = PenaltyService(self.db)
            created = penalty_service.check_and_create_missing_report_penalties()

            from services.notifications import notify_penalty_created
            for item in created:
                notify_penalty_created(
                    user_name=item.user_name,
                    bale_id=item.bale_id,
                    date_shamsi=item.date_shamsi,
                    amount=item.amount,
                )

            if created:
                msg = f"✅ {len(created)} جریمه جدید ایجاد شد:\n\n"
                for item in created:
                    msg += f"❌ {item.user_name} — {item.amount:,} تومان ({item.date_shamsi})\n"
            else:
                msg = "✅ هیچ جریمه جدیدی ایجاد نشد."
            
            await client.send_message(
                chat_id=message.chat.id,
                text=msg,
            )
            
            logger.info(f"Manual penalty check: {len(created)} penalties created")
        
        except Exception as e:
            logger.error(f"Error in manual penalty check: {e}")
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ خطا: {str(e)}",
            )
