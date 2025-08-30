import discord
from discord import app_commands
from discord.ext import commands
from config import Config
from .database import db
from bot.cogs.find import FindCog
from bot.cogs.profile import ProfileCog
from bot.cogs.feedback import FeedbackCog
from bot.cogs.team import TeamCog
from bot.cogs.volunteer import VolunteerCog
from bot.cogs.email_assistant import EmailAssistantCog
import logging
import datetime

class MaximallyBot(commands.Bot):
    def __init__(self):
        # Configure intents explicitly. Slash commands don't require message_content,
        # but other features may. Enable it here and remind to toggle in Dev Portal.
        intents = discord.Intents.all()
        intents.guilds = True
        intents.members = True
        intents.message_content = True  # Requires enabling in Discord Developer Portal

        super().__init__(
            command_prefix="!",
            intents=intents,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="you all...!"
            )
        )
        self.logger = logging.getLogger(__name__)
        self.config = Config
        self.start_time = datetime.datetime.utcnow()
        self.logger.info("Intents configured: guilds=%s, members=%s, message_content=%s",
                        intents.guilds, intents.members, intents.message_content)
        self.logger.info("If you still see a message_content warning, enable 'MESSAGE CONTENT INTENT' in the Discord Developer Portal for this bot.")

    async def setup_hook(self):
        await self.add_cog(ProfileCog(self))
        await self.add_cog(FindCog(self))
        await self.add_cog(FeedbackCog(self))
        await self.add_cog(TeamCog(self))
        await self.add_cog(VolunteerCog(self))
        await self.add_cog(EmailAssistantCog(self))

        if self.config.GUILD_ID:
            guild = discord.Object(id=self.config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

        self.logger.info("Commands synced")

    @app_commands.command(
        name="health",
        description="Check bot health and status"
    )
    async def health_check(self, interaction: discord.Interaction):
        """Health check command for monitoring."""
        try:
            # Check database connectivity
            db_status = "✅ Connected"
            try:
                # Quick database check
                from .database import db
                db.get_profile(0)  # This will fail but test connection
            except Exception:
                db_status = "❌ Database connection issue"

            # Check email system
            email_status = "✅ Configured"
            try:
                from bot.email.template_manager import template_manager
                templates = await template_manager.get_all_templates()
                email_status = f"✅ {len(templates)} templates loaded"
            except Exception as e:
                email_status = f"❌ Email system error: {str(e)[:50]}"

            # System info
            import psutil
            import platform

            memory = psutil.virtual_memory()
            memory_usage = f"{memory.percent:.1f}%"

            from bot.utils.embed import success_embed
            
            embed = success_embed(
                "Bot Health Check",
                "All systems operational and running smoothly!"
            )

            embed.add_field(
                name="💻 System Status",
                value=f"**Memory Usage:** {memory_usage}\n**Platform:** {platform.system()}",
                inline=False
            )

            embed.add_field(
                name="🗄️ Database",
                value=db_status,
                inline=True
            )

            embed.add_field(
                name="📧 Email System",
                value=email_status,
                inline=True
            )

            embed.add_field(
                name="⏰ Uptime",
                value=f"<t:{int(self.start_time.timestamp())}:R>",
                inline=True
            )

            embed.set_footer(text=f"Requested by {interaction.user.name} • Maximally : The global hackathon league")

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            from bot.utils.embed import error_embed
            
            embed = error_embed(
                "Health Check Failed",
                "Unable to retrieve system status at this time.",
                "Please try again in a few moments. If the issue persists, contact support."
            )
            
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                # Fallback to simple message if embed fails
                await interaction.response.send_message(
                    "❌ Health check failed - system temporarily unavailable",
                    ephemeral=True
                )

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")
        self.logger.info("Bot is ready and operational!")

    async def on_disconnect(self):
        self.logger.warning("Bot disconnected from Discord")

    async def on_resumed(self):
        self.logger.info("Bot connection resumed")

    async def on_error(self, event, *args, **kwargs):
        self.logger.error(f"Unhandled error in {event}: {args} {kwargs}")

    async def close(self):
        """Clean shutdown of the bot."""
        self.logger.info("Shutting down bot gracefully...")
        await super().close()
        self.logger.info("Bot shutdown complete")