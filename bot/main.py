import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
from bot.cogs.profile import ProfileCommands
from bot.cogs.find import FindCommands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

class MaximallyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix="!",
            intents=intents,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="hackers build the future"
            )
        )
        self.guild_id = int(os.getenv("GUILD_ID"))

    async def setup_hook(self):
        # Register application commands
        self.tree.add_command(ProfileCommands(), guild=discord.Object(id=self.guild_id))
        self.tree.add_command(FindCommands(), guild=discord.Object(id=self.guild_id))
        
        # Sync commands to specific guild
        await self.tree.sync(guild=discord.Object(id=self.guild_id))
        logger.info("Commands synced")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")

bot = MaximallyBot()
bot.run(os.getenv("DISCORD_TOKEN"))