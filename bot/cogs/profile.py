import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils import validation
from bot.utils.embed import profile_embed

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(
        name="profile",
        description="Create or update your profile"
    )
    @app_commands.describe(
        name="Your full name",
        skills="Your skills (comma separated)",
        interests="Your interests (comma separated)"
    )
    async def profile_command(
        self,
        interaction: discord.Interaction,
        name: str,
        skills: str = "",
        interests: str = ""
    ):
        try:
            # Validate inputs
            name = validation.validate_name(name)
            skills = validation.validate_skills(skills)
            interests = validation.validate_interests(interests)
            
            # Save to database
            discord_id = str(interaction.user.id)
            discord_username = f"{interaction.user.name}#{interaction.user.discriminator}"
            
            db.upsert_profile(
                discord_id, 
                discord_username, 
                name, 
                skills, 
                interests
            )
            
            # Create response
            profile = {
                'name': name,
                'discord_username': discord_username,
                'skills': skills,
                'interests': interests
            }
            embed = profile_embed(profile)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.logger.info(f"Profile updated for {discord_username}")
            
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Validation error: {str(e)}", 
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Profile command error: {str(e)}")
            await interaction.response.send_message(
                "❌ Failed to save profile. Please try again later.", 
                ephemeral=True
            )