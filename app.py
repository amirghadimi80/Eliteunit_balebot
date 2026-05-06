"""
Main application entry point for EliteUniteTime system.
"""

import logging
import os
import sys
import io
from pathlib import Path

# Setup logging with UTF-8 encoding to fix UnicodeEncodeError on Windows
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            Path(__file__).parent / "logs" / "app.log",
            encoding="utf-8",
        ),
        logging.StreamHandler(
            stream=io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
        ),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the application.
    Initializes and starts the bot.
    """
    try:
        logger.info("=" * 50)
        logger.info("EliteUniteTime Bot Starting...")
        logger.info("=" * 50)
        
        # Check if API token is set
        from config.settings import BALE_API_TOKEN
        
        if not BALE_API_TOKEN:
            logger.error("BALE_API_TOKEN is not set in environment variables")
            print("❌ Error: BALE_API_TOKEN not configured")
            print("Please set BALE_API_TOKEN in your .env file")
            sys.exit(1)
        
        # Import bot
        from bot import EliteUniteTimeBot
        
        # Create bot instance
        bot = EliteUniteTimeBot()
        
        # Start bot
        bot.start()
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
