import logging
from bot.core.logger import setup_logging
from bot.core.bot import MaximallyBot
from config import Config

setup_logging(level=Config.LOG_LEVEL)

if __name__ == "__main__":
    bot = MaximallyBot()
    bot.run(Config.DISCORD_TOKEN)