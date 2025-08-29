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
            if not skills and not interests:
                await interaction.response.send_message(
                    "⚠️ Please provide at least one search criteria", 
                    ephemeral=True
                )
                return
            
            results = db.search_profiles(
                skills=skills,
                interests=interests,
                limit=limit
            )
            
            if not results:
                await interaction.response.send_message(
                    "🔍 No profiles found matching your criteria",
                    ephemeral=True
                )
                return
            
            embed = search_results_embed(results)
            await interaction.response.send_message(embed=embed)
            self.logger.info(f"Search completed for {interaction.user}")

        except Exception as e:
            self.logger.error(f"Find command error: {str(e)}")
            await interaction.response.send_message(
                "❌ Error searching profiles. Please try again later.", 
                ephemeral=True
            )