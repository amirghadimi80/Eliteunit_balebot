"""
Penalty payment handler — receipt upload and group notification.
"""

import logging
from typing import Optional

from balethon import Client
from balethon.objects import Message, InlineKeyboard, InlineKeyboardButton

from database.db import Database
from services.penalty import PenaltyService
from services.notifications import send_receipt_to_groups
from config.settings import (
    PAYMENT_CARD_HOLDER,
    PAYMENT_CARD_NUMBER,
)
from utils.formatter import MessageFormatter

logger = logging.getLogger(__name__)


class PenaltyPaymentHandler:
    """Handle in-bot penalty payment with receipt photo."""

    def __init__(self, db: Database):
        self.db = db
        self.penalty_service = PenaltyService(db)
        self.user_states = {}

    def _chat_id(self, message: Message) -> int:
        return message.chat.id if message.chat else 0

    @staticmethod
    def _get_image_file_id(message: Message) -> Optional[str]:
        if message.photo:
            return message.photo[-1].id
        if message.document:
            mime = getattr(message.document, "mime_type", "") or ""
            if mime.startswith("image/"):
                return message.document.id
        return None

    async def handle_pay_penalty_start(self, client: Client, message: Message):
        """Show unpaid penalty summary and ask for receipt."""
        chat_id = self._chat_id(message)
        user = self.db.get_user_by_bale_id(chat_id)

        if not user:
            await client.send_message(
                chat_id=chat_id,
                text="❌ لطفاً ابتدا از طریق /start ثبت نام کنید.",
            )
            return

        unpaid = self.penalty_service.get_user_unpaid_penalties(user.id)
        if not unpaid:
            keyboard = InlineKeyboard()
            keyboard.add_row(
                InlineKeyboardButton(
                    text="🏠 بازگشت به منوی اصلی",
                    callback_data="main_menu",
                )
            )
            await client.send_message(
                chat_id=chat_id,
                text="✅ شما جریمه پرداخت‌نشده‌ای ندارید.",
                reply_markup=keyboard,
            )
            return

        days_count = len(unpaid)
        total_amount = sum(p.amount for p in unpaid)
        dates_list = "\n".join(f"• {p.date_shamsi}" for p in unpaid[:10])
        if days_count > 10:
            dates_list += f"\n• ... و {days_count - 10} روز دیگر"

        self.user_states[chat_id] = {
            "state": "waiting_receipt",
            "user_id": user.id,
            "days_count": days_count,
            "total_amount": total_amount,
        }

        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="❌ انصراف",
                callback_data="main_menu",
            )
        )

        await client.send_message(
            chat_id=chat_id,
            text=(
                f"💳 پرداخت جریمه\n\n"
                f"📅 تعداد روز گزارش ثبت‌نشده: {days_count} روز\n"
                f"💰 مبلغ قابل پرداخت: {total_amount:,} تومان\n\n"
                f"روزهای جریمه:\n{dates_list}\n\n"
                f"لطفاً به کارت زیر واریز کنید:\n"
                f"💳 {PAYMENT_CARD_NUMBER}\n"
                f"به نام {PAYMENT_CARD_HOLDER}\n\n"
                f"📸 بعد از پرداخت، تصویر رسید را همین‌جا بفرستید."
            ),
            reply_markup=keyboard,
        )

    async def handle_receipt_upload(self, client: Client, message: Message):
        """Process receipt photo and mark all unpaid penalties as paid."""
        chat_id = self._chat_id(message)
        user_data = self.user_states.get(chat_id)

        if not user_data or user_data.get("state") != "waiting_receipt":
            return False

        file_id = self._get_image_file_id(message)
        if not file_id:
            await client.send_message(
                chat_id=chat_id,
                text="❌ لطفاً تصویر رسید را بفرستید (عکس).",
            )
            return True

        user_db_id = user_data["user_id"]
        user = self.db.get_user_by_id(user_db_id)
        if not user:
            del self.user_states[chat_id]
            await client.send_message(chat_id=chat_id, text="❌ کاربر یافت نشد.")
            return True

        unpaid = self.penalty_service.get_user_unpaid_penalties(user_db_id)
        if not unpaid:
            del self.user_states[chat_id]
            await client.send_message(
                chat_id=chat_id,
                text="✅ جریمه پرداخت‌نشده‌ای ندارید.",
            )
            return True

        days_count = len(unpaid)
        total_amount = sum(p.amount for p in unpaid)

        paid_days, paid_amount = self.penalty_service.pay_all_unpaid_penalties(user_db_id)
        if paid_days == 0:
            await client.send_message(
                chat_id=chat_id,
                text="❌ خطا در ثبت پرداخت. لطفاً دوباره تلاش کنید.",
            )
            return True

        del self.user_states[chat_id]

        caption = MessageFormatter.format_penalty_payment_receipt_caption(
            user.full_name, paid_amount, paid_days
        )

        groups_sent = await send_receipt_to_groups(
            client, message, file_id, caption
        )
        if groups_sent == 0:
            logger.warning("Receipt was not sent to any group")

        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="🏠 بازگشت به منوی اصلی",
                callback_data="main_menu",
            )
        )

        await client.send_message(
            chat_id=chat_id,
            text=(
                f"✅ پرداخت شما ثبت شد!\n\n"
                f"📅 {paid_days} روز جریمه — {paid_amount:,} تومان\n"
                f"رسید در گروه ارسال شد.\n\n"
                f"ممنون {user.full_name} 🙏"
            ),
            reply_markup=keyboard,
        )

        logger.info(
            f"Penalty paid via bot: {user.full_name}, "
            f"{paid_days} days, {paid_amount} Toman"
        )
        return True

    def cancel_payment(self, chat_id: int) -> None:
        self.user_states.pop(chat_id, None)
