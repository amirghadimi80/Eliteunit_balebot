"""
Main Bale bot initialization and message routing.
Handles all incoming messages and callback queries.
"""

import logging
import sys
from balethon import Client
from balethon.objects import CallbackQuery, Message

from database.db import Database
from services.scheduler import SchedulerService
from handlers.start import StartHandler
from handlers.tasks import TaskHandler
from handlers.profile import ProfileHandler
from handlers.admin import AdminHandler
from config.settings import BALE_API_TOKEN

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class EliteUniteTimeBot:
    """Main bot class for EliteUniteTime system."""
    
    def __init__(self):
        """Initialize bot with all handlers and services."""
        # Initialize database
        self.db = Database()
        logger.info("Database initialized")
        
        # Initialize services
        self.scheduler_service = SchedulerService(self.db)
        logger.info("Scheduler service initialized")
        
        # Initialize handlers
        self.start_handler = StartHandler(self.db)
        self.task_handler = TaskHandler(self.db)
        self.profile_handler = ProfileHandler(self.db)
        self.admin_handler = AdminHandler(self.db)
        logger.info("All handlers initialized")
        
        # Initialize bot client
        self.client = Client(token=BALE_API_TOKEN)
        logger.info("Bale client initialized")
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message and callback handlers."""
        # Register callback query handler FIRST (before message handler)
        self.client.on_callback_query()(self._handle_callback_query)
        # Register message handler
        self.client.on_message()(self._handle_message)
        logger.info("Message and callback handlers registered")
    
    async def _handle_message(self, client: Client, message: Message):
        """
        Handle incoming messages.
        Routes messages to appropriate handlers.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        try:
            # Get user ID safely
            if message.author:
                user_id = message.author.id
            elif message.chat:
                user_id = message.chat.id
            else:
                logger.warning("Message with no author or chat, skipping")
                return

            text = message.text or ""
            
            logger.info(f"Message from user {user_id}: {text[:50]}")
            
            # Check if message is contact sharing (for registration)
            if message.contact:
                await self.start_handler.handle_phone_input(client, message)
                return
            
            # Handle commands
            if text.startswith("/start"):
                await self.start_handler.handle_start(client, message)
                return
            
            # /admin command removed — use web dashboard instead
            
            # Handle text input for ongoing flows - check start handler states first
            user_state = self.start_handler.user_states.get(user_id)
            
            if user_state:
                state = user_state.get("state")
                if state == "waiting_name":
                    await self.start_handler.handle_name_input(client, message)
                    return
                elif state == "waiting_phone":
                    # Manual phone number input
                    await self.start_handler.handle_phone_input(client, message)
                    return
            
            # Check task handler states
            user_state = self.task_handler.user_states.get(user_id)
            
            if user_state:
                if user_state.get("state") == "waiting_main_hours":
                    await self.task_handler.handle_main_hours_input(client, message)
                    return
                elif user_state.get("state") == "waiting_side_hours":
                    await self.task_handler.handle_side_hours_input(client, message)
                    return
            
            # Check profile handler states
            user_state = self.profile_handler.user_states.get(user_id)
            
            if user_state:
                if user_state.get("state") == "waiting_bio":
                    await self.profile_handler.handle_bio_input(client, message)
                    return
                elif user_state.get("state") == "waiting_interests":
                    await self.profile_handler.handle_interests_input(client, message)
                    return
            
            # If no specific handler, suggest commands
            await client.send_message(
                chat_id=user_id,
                text=(
                    "👋 درود!\n\n"
                    "دستورات موجود:\n"
                    "/start - شروع/ثبت نام"
                ),
            )
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            try:
                chat_id = message.chat.id if message.chat else None
                if chat_id:
                    await client.send_message(
                        chat_id=chat_id,
                        text="❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
                    )
            except Exception:
                pass
    
    async def _handle_callback_query(self, client: Client, callback_query: CallbackQuery):
        """
        Handle callback queries from inline buttons.
        
        Args:
            client: Balethon client instance
            callback_query: CallbackQuery object
        """
        try:
            # Get user_id safely
            if hasattr(callback_query, 'author') and callback_query.author:
                user_id = callback_query.author.id
            elif callback_query.message and callback_query.message.chat:
                user_id = callback_query.message.chat.id
            else:
                logger.warning("CallbackQuery with no user info, skipping")
                return

            data = callback_query.data or ""
            
            logger.info(f"Callback query from user {user_id}: {data}")
            
            # Route to appropriate handler based on callback data
            if data == "daily_report":
                await self.task_handler.handle_daily_report_start(client, callback_query.message)
            
            elif data == "main_menu":
                await self.start_handler._show_main_menu(client, callback_query.message)
            
            elif data == "weekly_report":
                await self.task_handler.handle_weekly_report(client, callback_query.message)
            
            elif data == "monthly_report":
                await self.task_handler.handle_monthly_report(client, callback_query.message)
            
            elif data == "profile":
                await self.profile_handler.handle_profile_view(client, callback_query.message)
            
            elif data == "edit_profile":
                await self.profile_handler.handle_edit_profile(client, callback_query.message)
            
            elif data == "edit_bio":
                await self.profile_handler.handle_edit_bio(client, callback_query.message)
            
            elif data == "edit_interests":
                await self.profile_handler.handle_edit_interests(client, callback_query.message)
            
            elif data == "friends":
                await self.profile_handler.handle_friends_discovery(client, callback_query.message)
            
            elif data.startswith("view_user_"):
                user_id_to_view = int(data.split("_")[2])
                await self.profile_handler.handle_view_user_profile(client, callback_query.message, user_id_to_view)
            
            elif data == "admin_view_users":
                await self.admin_handler.handle_view_all_users(client, callback_query.message)
            
            elif data == "admin_weekly_report":
                await self.admin_handler.handle_weekly_report_admin(client, callback_query.message)
            
            elif data == "admin_export_excel":
                await self.admin_handler.handle_export_excel(client, callback_query.message)
            
            elif data == "admin_penalties":
                await self.admin_handler.handle_penalties_management(client, callback_query.message)
            
            elif data == "admin_manual_check":
                await self.admin_handler.handle_manual_penalty_check(client, callback_query.message)
            
            # Answer callback query to remove loading state
            try:
                await callback_query.answer(text="")
            except Exception:
                pass
        
        except Exception as e:
            logger.error(f"Error handling callback query: {e}", exc_info=True)
    
    def start(self):
        """Start the bot and scheduler."""
        logger.info("Starting EliteUniteTime bot...")
        
        # Set bot instance in scheduler
        self.scheduler_service.set_bot_instance(self.client)
        
        # Start scheduler
        try:
            self.scheduler_service.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
        
        # Start bot
        try:
            self.client.run()
            logger.info("Bot started successfully")
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting bot: {e}", exc_info=True)
            sys.exit(1)
    
    def stop(self):
        """Stop the bot and scheduler."""
        logger.info("Stopping EliteUniteTime bot...")
        
        try:
            self.scheduler_service.stop()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        logger.info("Bot stopped")
