import discord
from discord import app_commands
from discord.ext import commands
import csv
import os
from datetime import datetime

class FeedbackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.feedback_file = "feedback.csv"
        
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "User ID", "Username", "Feedback"])

    @app_commands.command(
        name="feedback",
        description="Send feedback to the bot developer"
    )
    @app_commands.describe(
        message="Your feedback or suggestions"
    )
    async def feedback_command(
        self,
        interaction: discord.Interaction,
        message: str
    ):
        try:
            # Defer the response since we do file I/O operations
            await interaction.response.defer(ephemeral=True)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_id = interaction.user.id
            username = f"{interaction.user.name}"

            with open(self.feedback_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, user_id, username, message])

            await interaction.followup.send(
                "✅ Thank you for your feedback! We appreciate your input.",
                ephemeral=True
            )
            self.logger.info(f"Feedback received from {username}")

        except Exception as e:
            self.logger.error(f"Feedback command error: {str(e)}")
            try:
                await interaction.followup.send(
                    "❌ Failed to save feedback. Please try again later.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

async def setup(bot):
    await bot.add_cog(FeedbackCog(bot))