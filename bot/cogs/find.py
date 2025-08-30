import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils.embed import search_results_embed

class FindCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(
        name="find",
        description="Find Users by skills or interests"
    )
    @app_commands.describe(
        skills="Skills to search (comma separated)",
        interests="Interests to search (comma separated)",
        limit="Number of results to show (1-20)"
    )
    async def find_command(
        self,
        interaction: discord.Interaction,
        skills: str = "",
        interests: str = "",
        limit: app_commands.Range[int, 1, 20] = 10
    ):
        try:
            # Check if interaction is still valid
            if interaction.is_expired():
                self.logger.warning("Interaction has expired, cannot respond")
                return

            # Defer the response since we do database operations
            try:
                await interaction.response.defer(ephemeral=True)
            except discord.errors.InteractionResponded:
                self.logger.warning("Interaction already responded to")
                return

            if not skills and not interests:
                try:
                    await interaction.followup.send(
                        "[WARNING] Please provide at least one search criteria",
                        ephemeral=True
                    )
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send search criteria warning - interaction already handled")
                return

            results = db.search_profiles(
                skills=skills,
                interests=interests,
                limit=limit
            )

            if not results:
                try:
                    await interaction.followup.send(
                        "[SEARCH] No profiles found matching your criteria",
                        ephemeral=True
                    )
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send no results message - interaction already handled")
                return

            embed = search_results_embed(results)
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.NotFound):
                self.logger.warning("Could not send search results - interaction already handled")
            self.logger.info(f"Search completed for {interaction.user}")

        except Exception as e:
            self.logger.error(f"Find command error: {str(e)}")
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(
                        "[ERROR] Error searching profiles. Please try again later.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                self.logger.error(f"Failed to send find error followup: {followup_error}")