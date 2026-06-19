"""
Daily report submission handler.
"""

import logging
from balethon import Client
from balethon.objects import Message, InlineKeyboard, InlineKeyboardButton

from database.db import Database
from services.reports import ReportService
from config.settings import BUTTON_LABELS
from utils.date_utils import format_date_persian, get_today_gregorian, get_current_time_iran
from utils.formatter import MessageFormatter

logger = logging.getLogger(__name__)


class TaskHandler:
    """Handler for daily report submission and task management."""
    
    def __init__(self, db: Database):
        """
        Initialize task handler.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.report_service = ReportService(db)
        self.user_states = {}  # Track user report submission state
    
    async def handle_daily_report_start(self, client: Client, message: Message):
        """
        Start daily report submission flow.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user = self.db.get_user_by_bale_id(user_id)
        
        if not user:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً ابتدا از طریق /start ثبت نام کنید.",
            )
            return
        
        target_date, is_backdated = self.report_service.get_next_report_date(user.id)
        date_gregorian = target_date.strftime("%Y-%m-%d")

        if self.db.report_exists(user.id, date_gregorian):
            await client.send_message(
                chat_id=user_id,
                text=f"✅ گزارش روز {format_date_persian(target_date)} قبلاً ثبت شده است.",
            )
            return

        # Initialize user state
        self.user_states[user_id] = {
            "state": "waiting_main_hours",
            "user_id": user.id,
            "report_date": target_date,
        }

        target_date_persian = format_date_persian(target_date)

        if is_backdated:
            message_text = (
                f"📊 ثبت گزارش روزانه\n\n"
                f"⚠️ گزارش روزهای قبل ثبت نشده.\n"
                f"اول این گزارش را وارد کنید، بعد گزارش امروز.\n\n"
                f"📅 تاریخ: {target_date_persian}\n\n"
                f"⬛️ لطفاً ساعت کاری اصلی را وارد کنید:\n"
                f"(مثال: 6 یا 6.5)"
            )
        else:
            message_text = (
                f"📊 ثبت گزارش روزانه\n\n"
                f"📅 امروز: {target_date_persian}\n\n"
                f"⬛️ لطفاً ساعت کاری اصلی را وارد کنید:\n"
                f"(مثال: 6 یا 6.5)"
            )
        
        await client.send_message(
            chat_id=user_id,
            text=message_text,
        )
    
    async def handle_main_hours_input(self, client: Client, message: Message):
        """
        Handle main working hours input.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user_data = self.user_states.get(user_id)
        
        if not user_data or user_data.get("state") != "waiting_main_hours":
            return
        
        try:
            main_hours = float(message.text.strip())
            
            if main_hours < 0 or main_hours > 12:
                await client.send_message(
                    chat_id=user_id,
                    text="❌ ساعات اصلی باید بین 0 تا 12 باشد.",
                )
                return
            
            # Update state
            user_data["state"] = "waiting_side_hours"
            user_data["main_hours"] = main_hours
            
            # Ask for side hours
            message_text = (
                f"🔵 لطفاً ساعت کاری فرعی را وارد کنید:\n"
                f"(ورزش، پادکست، یادگیری، ...)\n\n"
                f"(مثال: 2 یا 2.5)"
            )
            
            await client.send_message(
                chat_id=user_id,
                text=message_text,
            )
        
        except ValueError:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً یک عدد معتبر وارد کنید.",
            )
    
    async def handle_side_hours_input(self, client: Client, message: Message):
        """
        Handle side working hours input and submit report.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user_data = self.user_states.get(user_id)
        
        if not user_data or user_data.get("state") != "waiting_side_hours":
            return
        
        try:
            side_hours = float(message.text.strip())
            
            if side_hours < 0 or side_hours > 8:
                await client.send_message(
                    chat_id=user_id,
                    text="❌ ساعات فرعی باید بین 0 تا 8 باشد.",
                )
                return
            
            # Submit report
            main_hours = user_data.get("main_hours")
            user_db_id = user_data.get("user_id")
            report_date = user_data.get("report_date") or get_today_gregorian()

            success, msg = self.report_service.submit_daily_report(
                user_db_id,
                main_hours,
                side_hours,
                report_date=report_date,
            )
            
            if success:
                # Clear user state
                del self.user_states[user_id]
                
                # Get report details
                user = self.db.get_user_by_id(user_db_id)
                now_time = get_current_time_iran().strftime("%H:%M")
                next_date, still_backdated = self.report_service.get_next_report_date(user_db_id)

                follow_up = ""
                if still_backdated:
                    follow_up = (
                        f"\n\n⚠️ هنوز گزارش روز {format_date_persian(next_date)} "
                        f"ثبت نشده.\n"
                        f"دوباره «ثبت گزارش روزانه» را بزنید."
                    )
                elif report_date != get_today_gregorian():
                    follow_up = (
                        "\n\n✅ حالا می‌توانید گزارش امروز را ثبت کنید."
                    )

                # Send confirmation to user with back button
                keyboard = InlineKeyboard()
                keyboard.add_row(
                    InlineKeyboardButton(
                        text="🏠 بازگشت به منوی اصلی",
                        callback_data="main_menu",
                    )
                )
                
                confirmation = (
                    f"✅ گزارش شما ثبت شد!\n\n"
                    f"👤 {user.full_name}\n"
                    f"⬛️ اصلی: {main_hours}\n"
                    f"🔵 فرعی: {side_hours}\n"
                    f"➕ مجموع: {main_hours + side_hours}\n\n"
                    f"📅 {format_date_persian(report_date)}\n"
                    f"🕐 ساعت ثبت: {now_time}"
                    f"{follow_up}"
                )
                
                await client.send_message(
                    chat_id=user_id,
                    text=confirmation,
                    reply_markup=keyboard,
                )
                
                # Send group notification
                await self._send_group_notification(
                    client, user, main_hours, side_hours, report_date
                )
                
                logger.info(f"Report submitted: user={user.full_name}, main={main_hours}, side={side_hours}")
            else:
                await client.send_message(
                    chat_id=user_id,
                    text=f"❌ {msg}",
                )
        
        except ValueError:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً یک عدد معتبر وارد کنید.",
            )
    
    async def _send_group_notification(self, client: Client, user, main_hours, side_hours, report_date):
        """
        Send report notification to group.
        
        Args:
            client: Balethon client instance
            user: User object
            main_hours: Main hours
            side_hours: Side hours
            report_date: Report date
        """
        from config.settings import BALE_GROUP_IDS
        from utils.date_utils import get_current_time_iran
        
        total = main_hours + side_hours
        now_time = get_current_time_iran().strftime("%H:%M")
        message = MessageFormatter.format_daily_report_group(
            user.full_name,
            main_hours,
            side_hours,
            total,
            report_date,
            submit_time=now_time,
        )
        
        if not BALE_GROUP_IDS:
            logger.warning("BALE_GROUP_ID not set, skipping group notification")
            return

        for group_id in BALE_GROUP_IDS:
            try:
                await client.send_message(
                    chat_id=group_id,
                    text=message,
                )
                logger.info(
                    f"Group notification sent to {group_id} for user {user.full_name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to send group notification to {group_id}: {e}"
                )
    
    async def handle_weekly_report(self, client: Client, message: Message):
        """
        Handle weekly report request.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user = self.db.get_user_by_bale_id(user_id)
        
        if not user:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً ابتدا ثبت نام کنید.",
            )
            return
        
        stats = self.report_service.get_weekly_stats(user.id)
        
        report_message = MessageFormatter.format_weekly_report(
            user.full_name,
            stats.week_start,
            stats.week_end,
            stats.main_hours,
            stats.side_hours,
            stats.total_hours,
        )
        
        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="🏠 بازگشت به منوی اصلی",
                callback_data="main_menu",
            )
        )
        
        await client.send_message(
            chat_id=user_id,
            text=report_message,
            reply_markup=keyboard,
        )
    
    async def handle_monthly_report(self, client: Client, message: Message):
        """
        Handle monthly report request.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user = self.db.get_user_by_bale_id(user_id)
        
        if not user:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً ابتدا ثبت نام کنید.",
            )
            return
        
        stats = self.report_service.get_monthly_stats(user.id)
        
        report_message = MessageFormatter.format_monthly_report(
            user.full_name,
            stats.year,
            stats.month,
            stats.main_hours,
            stats.side_hours,
            stats.total_hours,
            stats.days_reported,
            stats.days_total,
        )
        
        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="🏠 بازگشت به منوی اصلی",
                callback_data="main_menu",
            )
        )
        
        await client.send_message(
            chat_id=user_id,
            text=report_message,
            reply_markup=keyboard,
        )
