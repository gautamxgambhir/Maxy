import logging
import sys
import signal
import asyncio
import os
from bot.core.logger import setup_logging
from bot.core.bot import MaximallyBot
from config import config as Config

def validate_config():
    """Validate required configuration before starting."""
    required_vars = ['DISCORD_TOKEN']
    missing = []

    for var in required_vars:
        if not getattr(Config, var, None):
            missing.append(var)

    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)

    # Validate token format
    if not Config.DISCORD_TOKEN or len(Config.DISCORD_TOKEN) < 50:
        print("[ERROR] Invalid Discord token format")
        sys.exit(1)

    print("[INFO] Configuration validated successfully")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

async def main():
    """Main async function for bot startup."""
    # Setup basic logging first for error handling
    log_file = os.getenv("LOG_FILE", "logs/bot.log")
    setup_logging(level=Config.LOG_LEVEL, log_file=log_file)
    logger = logging.getLogger(__name__)

    try:
        # Validate configuration
        validate_config()

        logger.info("Starting Maximally Discord Bot...")

        # Create and start bot
        bot = MaximallyBot()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("🤖 Bot starting up...")
        await bot.start(Config.DISCORD_TOKEN)

    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())