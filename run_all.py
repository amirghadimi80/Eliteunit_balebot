"""
Runs both the Bale bot and the Flask dashboard concurrently.
Usage: python run_all.py
"""

import logging
import os
import sys
import io
import threading
from pathlib import Path

# ── Logging ──────────────────────────────────────────────
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


def run_dashboard():
    """Start the Flask dashboard in a background thread."""
    try:
        from dashboard.app import app
        port = int(os.getenv("DASHBOARD_PORT", 5000))
        logger.info(f"Dashboard starting on http://0.0.0.0:{port}")
        # use_reloader=False is required when running inside a thread
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)


def run_bot():
    """Start the Bale bot (blocking)."""
    from config.settings import BALE_API_TOKEN
    if not BALE_API_TOKEN:
        logger.error("BALE_API_TOKEN is not set in .env")
        sys.exit(1)

    from bot import EliteUniteTimeBot
    bot = EliteUniteTimeBot()
    bot.start()


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("  EliteUniteTime — Bot + Dashboard")
    logger.info("=" * 50)

    # Dashboard runs in a daemon thread (dies when main thread dies)
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True, name="Dashboard")
    dashboard_thread.start()
    logger.info("Dashboard thread started")

    # Bot runs in the main thread (blocking)
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Stopped by user — Goodbye!")
