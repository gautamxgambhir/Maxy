import discord
from discord.ext import commands
from config import Config
from .database import db
from bot.cogs.find import FindCog
from bot.cogs.profile import ProfileCog
import logging

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
        self.logger = logging.getLogger(__name__)
        self.config = Config

    async def setup_hook(self):
        # Add cogs
        await self.add_cog(ProfileCog(self))
        await self.add_cog(FindCog(self))
        
        # Sync commands
        if self.config.GUILD_ID:
            guild = discord.Object(id=self.config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        
        self.logger.info("Commands synced")

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info("------")