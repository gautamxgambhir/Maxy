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
        name="register-profile",
        description="Create your profile"
    )
    @app_commands.describe(
        name="Your full name",
        skills="Your skills (comma separated)",
        interests="Your interests (comma separated)"
    )
    async def register_profile(
        self,
        interaction: discord.Interaction,
        name: str,
        skills: str,
        interests: str
    ):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            name = validation.validate_name(name)
            skills = validation.validate_skills(skills)
            interests = validation.validate_interests(interests)

            discord_id = str(interaction.user.id)
            discord_username = f"{interaction.user.name}"

            db.upsert_profile(
                discord_id,
                discord_username,
                name,
                skills,
                interests
            )

            profile = {
                'name': name,
                'discord_username': discord_username,
                'skills': skills,
                'interests': interests
            }
            embed = profile_embed(profile)

            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
                content="✅ Profile created successfully!"
            )
            self.logger.info(f"Profile registered for {discord_username}")

        except ValueError as e:
            try:
                await interaction.followup.send(
                    f"❌ Validation error: {str(e)}",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")
        except Exception as e:
            self.logger.error(f"Profile registration error: {str(e)}")
            try:
                await interaction.followup.send(
                    "❌ Failed to create profile. Please try again later.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @app_commands.command(
        name="edit-profile",
        description="Update your profile"
    )
    @app_commands.describe(
        name="Your full name (leave blank to keep current)",
        skills="Your skills (comma separated, leave blank to keep current)",
        interests="Your interests (comma separated, leave blank to keep current)"
    )
    async def edit_profile(
        self,
        interaction: discord.Interaction,
        name: str = None,
        skills: str = None,
        interests: str = None
    ):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            discord_id = str(interaction.user.id)
            current_profile = db.get_profile(discord_id)

            if not current_profile:
                await interaction.followup.send(
                    "❌ You don't have a profile yet. Use `/register-profile` first.",
                    ephemeral=True
                )
                return

            name = name or current_profile['name']
            skills = skills or current_profile['skills']
            interests = interests or current_profile['interests']

            name = validation.validate_name(name)
            skills = validation.validate_skills(skills)
            interests = validation.validate_interests(interests)

            discord_username = f"{interaction.user.name}"

            db.upsert_profile(
                discord_id,
                discord_username,
                name,
                skills,
                interests
            )

            profile = {
                'name': name,
                'discord_username': discord_username,
                'skills': skills,
                'interests': interests
            }
            embed = profile_embed(profile)

            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
                content="✅ Profile updated successfully!"
            )
            self.logger.info(f"Profile updated for {discord_username}")

        except ValueError as e:
            try:
                await interaction.followup.send(
                    f"❌ Validation error: {str(e)}",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")
        except Exception as e:
            self.logger.error(f"Profile edit error: {str(e)}")
            try:
                await interaction.followup.send(
                    "❌ Failed to update profile. Please try again later.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @app_commands.command(
        name="view-profile",
        description="View your profile"
    )
    async def view_profile(
        self,
        interaction: discord.Interaction
    ):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            discord_id = str(interaction.user.id)
            profile = db.get_profile(discord_id)

            if not profile:
                await interaction.followup.send(
                    "❌ You don't have a profile yet. Use `/register-profile` to create one.",
                    ephemeral=True
                )
                return

            profile_data = {
                'name': profile['name'],
                'discord_username': profile['discord_username'],
                'skills': profile['skills'],
                'interests': profile['interests']
            }
            embed = profile_embed(profile_data)

            await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )
            self.logger.info(f"Profile viewed by {profile['discord_username']}")

        except Exception as e:
            self.logger.error(f"Profile view error: {str(e)}")
            try:
                await interaction.followup.send(
                    "❌ Failed to retrieve profile. Please try again later.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))