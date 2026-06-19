"""
Daily report submission handler.
"""

import logging
from datetime import date, datetime, timedelta

from balethon import Client
from balethon.objects import Message, InlineKeyboard, InlineKeyboardButton

from database.db import Database
from services.reports import ReportService
from utils.date_utils import (
    format_date_persian,
    get_today_gregorian,
    get_current_time_iran,
    is_within_report_grace_period,
    gregorian_to_jalali_str,
)
from utils.formatter import MessageFormatter

logger = logging.getLogger(__name__)


class TaskHandler:
    """Handler for daily report submission and task management."""

    def __init__(self, db: Database):
        self.db = db
        self.report_service = ReportService(db)
        self.user_states = {}

    def _chat_id(self, message: Message) -> int:
        return message.chat.id if message.chat else 0

    async def handle_daily_report_start(self, client: Client, message: Message):
        """Start daily report flow — show missing days or today's report."""
        chat_id = self._chat_id(message)
        user = self.db.get_user_by_bale_id(chat_id)

        if not user:
            await client.send_message(
                chat_id=chat_id,
                text="❌ لطفاً ابتدا از طریق /start ثبت نام کنید.",
            )
            return

        missing = self.report_service.get_missing_report_dates(user.id)
        if missing:
            await self._show_missing_days_picker(client, chat_id, user.id)
            return

        today = get_today_gregorian()
        if self.db.report_exists(user.id, today.strftime("%Y-%m-%d")):
            await client.send_message(
                chat_id=chat_id,
                text=f"✅ گزارش امروز ({format_date_persian(today)}) قبلاً ثبت شده است.",
            )
            return

        await self._start_report_entry(client, chat_id, user.id, today, is_today=True)

    async def handle_report_date_pick(
        self, client: Client, message: Message, date_gregorian: str
    ):
        """User picked a missing day from the inline list."""
        chat_id = self._chat_id(message)
        user = self.db.get_user_by_bale_id(chat_id)

        if not user:
            await client.send_message(
                chat_id=chat_id,
                text="❌ لطفاً ابتدا از طریق /start ثبت نام کنید.",
            )
            return

        try:
            picked = datetime.strptime(date_gregorian, "%Y-%m-%d").date()
        except ValueError:
            await client.send_message(chat_id=chat_id, text="❌ تاریخ نامعتبر است.")
            return

        missing = self.report_service.get_missing_report_dates(user.id)
        if not missing:
            await self.handle_daily_report_start(client, message)
            return

        if picked != missing[0]:
            await client.send_message(
                chat_id=chat_id,
                text=(
                    f"⚠️ لطفاً اول گزارش روز {format_date_persian(missing[0])} "
                    f"را ثبت کنید."
                ),
            )
            await self._show_missing_days_picker(client, chat_id, user.id)
            return

        await self._start_report_entry(client, chat_id, user.id, picked, is_today=False)

    async def _show_missing_days_picker(
        self, client: Client, chat_id: int, user_db_id: int
    ):
        """Show list of missing days; only the oldest is selectable."""
        missing = self.report_service.get_missing_report_dates(user_db_id)
        if not missing:
            today = get_today_gregorian()
            if not self.db.report_exists(user_db_id, today.strftime("%Y-%m-%d")):
                await self._start_report_entry(
                    client, chat_id, user_db_id, today, is_today=True
                )
            else:
                await client.send_message(
                    chat_id=chat_id,
                    text=f"✅ گزارش امروز ({format_date_persian(today)}) قبلاً ثبت شده است.",
                )
            return

        lines = ["📊 ثبت گزارش روزانه\n"]
        lines.append("⚠️ ابتدا گزارش روزهای زیر را ثبت کنید، بعد گزارش امروز:\n")

        keyboard = InlineKeyboard()
        for i, d in enumerate(missing):
            label = format_date_persian(d)
            if i == 0:
                lines.append(f"➡️ {label}  ← الان این روز")
                keyboard.add_row(
                    InlineKeyboardButton(
                        text=f"📝 ثبت {gregorian_to_jalali_str(d)}",
                        callback_data=f"report_pick_{d.strftime('%Y-%m-%d')}",
                    )
                )
            else:
                lines.append(f"⏳ {label}")

        lines.append(f"\n📌 {len(missing)} روز باقی‌مانده")

        keyboard.add_row(
            InlineKeyboardButton(
                text="🔄 بروزرسانی لیست",
                callback_data="daily_report",
            )
        )

        await client.send_message(
            chat_id=chat_id,
            text="\n".join(lines),
            reply_markup=keyboard,
        )

    async def _start_report_entry(
        self,
        client: Client,
        chat_id: int,
        user_db_id: int,
        report_date: date,
        is_today: bool,
    ):
        """Begin hours entry for a specific date."""
        date_gregorian = report_date.strftime("%Y-%m-%d")
        if self.db.report_exists(user_db_id, date_gregorian):
            await client.send_message(
                chat_id=chat_id,
                text=f"✅ گزارش روز {format_date_persian(report_date)} قبلاً ثبت شده است.",
            )
            return

        self.user_states[chat_id] = {
            "state": "waiting_main_hours",
            "user_id": user_db_id,
            "report_date": report_date,
        }

        target_persian = format_date_persian(report_date)
        if is_today:
            message_text = (
                f"📊 ثبت گزارش روزانه\n\n"
                f"📅 امروز: {target_persian}\n\n"
                f"⬛️ لطفاً ساعت کاری اصلی را وارد کنید:\n"
                f"(مثال: 6 یا 6.5)"
            )
        elif is_within_report_grace_period() and report_date == get_today_gregorian() - timedelta(days=1):
            message_text = (
                f"📊 ثبت گزارش روزانه\n\n"
                f"📅 گزارش دیروز: {target_persian}\n"
                f"⏰ مهلت: تا ساعت ۱۰ صبح امروز\n\n"
                f"⬛️ لطفاً ساعت کاری اصلی را وارد کنید:\n"
                f"(مثال: 6 یا 6.5)"
            )
        else:
            message_text = (
                f"📊 ثبت گزارش معوقه\n\n"
                f"📅 تاریخ: {target_persian}\n\n"
                f"⬛️ لطفاً ساعت کاری اصلی را وارد کنید:\n"
                f"(مثال: 6 یا 6.5)"
            )

        await client.send_message(chat_id=chat_id, text=message_text)

    async def handle_main_hours_input(self, client: Client, message: Message):
        """Handle main working hours input."""
        chat_id = self._chat_id(message)
        user_data = self.user_states.get(chat_id)

        if not user_data or user_data.get("state") != "waiting_main_hours":
            return

        try:
            main_hours = float(message.text.strip())

            if main_hours < 0 or main_hours > 12:
                await client.send_message(
                    chat_id=chat_id,
                    text="❌ ساعات اصلی باید بین 0 تا 12 باشد.",
                )
                return

            user_data["state"] = "waiting_side_hours"
            user_data["main_hours"] = main_hours

            await client.send_message(
                chat_id=chat_id,
                text=(
                    f"🔵 لطفاً ساعت کاری فرعی را وارد کنید:\n"
                    f"(ورزش، پادکست، یادگیری، ...)\n\n"
                    f"(مثال: 2 یا 2.5)"
                ),
            )

        except ValueError:
            await client.send_message(
                chat_id=chat_id,
                text="❌ لطفاً یک عدد معتبر وارد کنید.",
            )

    async def handle_side_hours_input(self, client: Client, message: Message):
        """Handle side hours input and submit report."""
        chat_id = self._chat_id(message)
        user_data = self.user_states.get(chat_id)

        if not user_data or user_data.get("state") != "waiting_side_hours":
            return

        try:
            side_hours = float(message.text.strip())

            if side_hours < 0 or side_hours > 8:
                await client.send_message(
                    chat_id=chat_id,
                    text="❌ ساعات فرعی باید بین 0 تا 8 باشد.",
                )
                return

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
                del self.user_states[chat_id]

                user = self.db.get_user_by_id(user_db_id)
                now_time = get_current_time_iran().strftime("%H:%M")
                is_late = report_date < get_today_gregorian()

                keyboard = InlineKeyboard()
                remaining = self.report_service.get_missing_report_dates(user_db_id)
                if remaining:
                    keyboard.add_row(
                        InlineKeyboardButton(
                            text="📝 ادامه ثبت گزارش‌های معوقه",
                            callback_data="daily_report",
                        )
                    )
                elif not self.db.report_exists(
                    user_db_id, get_today_gregorian().strftime("%Y-%m-%d")
                ):
                    keyboard.add_row(
                        InlineKeyboardButton(
                            text="📊 ثبت گزارش امروز",
                            callback_data="daily_report",
                        )
                    )
                else:
                    keyboard.add_row(
                        InlineKeyboardButton(
                            text="🏠 بازگشت به منوی اصلی",
                            callback_data="main_menu",
                        )
                    )

                follow_up = ""
                if remaining:
                    follow_up = (
                        f"\n\n⚠️ {len(remaining)} روز دیگر ثبت نشده.\n"
                        f"بعدی: {format_date_persian(remaining[0])}"
                    )
                elif report_date < get_today_gregorian():
                    follow_up = "\n\n✅ حالا می‌توانید گزارش امروز را ثبت کنید."

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
                    chat_id=chat_id,
                    text=confirmation,
                    reply_markup=keyboard,
                )

                await self._send_group_notification(
                    client, user, main_hours, side_hours, report_date, is_late=is_late
                )

                logger.info(
                    f"Report submitted: user={user.full_name}, "
                    f"date={report_date}, main={main_hours}, side={side_hours}"
                )
            else:
                await client.send_message(chat_id=chat_id, text=f"❌ {msg}")

        except ValueError:
            await client.send_message(
                chat_id=chat_id,
                text="❌ لطفاً یک عدد معتبر وارد کنید.",
            )

    async def _send_group_notification(
        self,
        client: Client,
        user,
        main_hours,
        side_hours,
        report_date,
        is_late: bool = False,
    ):
        """Send report notification to group."""
        from config.settings import BALE_GROUP_IDS

        total = main_hours + side_hours
        now_time = get_current_time_iran().strftime("%H:%M")
        message = MessageFormatter.format_daily_report_group(
            user.full_name,
            main_hours,
            side_hours,
            total,
            report_date,
            submit_time=now_time,
            is_late=is_late,
        )

        if not BALE_GROUP_IDS:
            logger.warning("BALE_GROUP_ID not set, skipping group notification")
            return

        for group_id in BALE_GROUP_IDS:
            try:
                await client.send_message(chat_id=group_id, text=message)
                logger.info(
                    f"Group notification sent to {group_id} for user {user.full_name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to send group notification to {group_id}: {e}"
                )

    async def handle_weekly_report(self, client: Client, message: Message):
        """Handle weekly report request."""
        chat_id = self._chat_id(message)
        user = self.db.get_user_by_bale_id(chat_id)

        if not user:
            await client.send_message(
                chat_id=chat_id,
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
            chat_id=chat_id,
            text=report_message,
            reply_markup=keyboard,
        )

    async def handle_monthly_report(self, client: Client, message: Message):
        """Handle monthly report request."""
        chat_id = self._chat_id(message)
        user = self.db.get_user_by_bale_id(chat_id)

        if not user:
            await client.send_message(
                chat_id=chat_id,
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
            chat_id=chat_id,
            text=report_message,
            reply_markup=keyboard,
        )
