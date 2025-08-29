import discord
from discord import app_commands
from discord.ext import commands

from bot.core.database import db
from bot.utils import embed as embed_utils


class VolunteerCog(commands.Cog):
    volunteer_group = app_commands.Group(name="volunteer", description="Volunteer management")

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @volunteer_group.command(name="add", description="Add a new volunteer task")
    async def add_task(self, interaction: discord.Interaction, title: str):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            user = interaction.user
            task_id = db.create_volunteer_task(title.strip(), str(user.id), user.display_name)
            row = db.get_volunteer_task_by_id(task_id)
            await interaction.followup.send(embed=embed_utils.volunteer_task_embed(row))
        except Exception as e:
            self.logger.error(f"/volunteer add failed: {e}")
            try:
                await interaction.followup.send("Failed to add task.", ephemeral=True)
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @volunteer_group.command(name="list", description="List all volunteer tasks")
    async def list_tasks(self, interaction: discord.Interaction):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            rows = db.get_all_volunteer_tasks()
            await interaction.followup.send(embed=embed_utils.volunteer_tasks_list_embed(rows))
        except Exception as e:
            self.logger.error(f"/volunteer list failed: {e}")
            try:
                await interaction.followup.send("Failed to list tasks.", ephemeral=True)
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @volunteer_group.command(name="join", description="Join a volunteer task")
    async def join_task(self, interaction: discord.Interaction, task_id: int):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            user = interaction.user
            ok = db.join_volunteer_task(task_id, str(user.id), user.display_name)
            if not ok:
                await interaction.followup.send("Task is not open or doesn't exist.", ephemeral=True)
                return
            row = db.get_volunteer_task_by_id(task_id)
            await interaction.followup.send(embed=embed_utils.volunteer_task_embed(row))
        except Exception as e:
            self.logger.error(f"/volunteer join failed: {e}")
            try:
                await interaction.followup.send("Failed to join task.", ephemeral=True)
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @volunteer_group.command(name="leave", description="Leave a volunteer task")
    async def leave_task(self, interaction: discord.Interaction, task_id: int):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            user = interaction.user
            ok = db.leave_volunteer_task(task_id, str(user.id))
            if not ok:
                await interaction.followup.send("You haven't joined this task.", ephemeral=True)
                return
            row = db.get_volunteer_task_by_id(task_id)
            await interaction.followup.send(embed=embed_utils.volunteer_task_embed(row))
        except Exception as e:
            self.logger.error(f"/volunteer leave failed: {e}")
            try:
                await interaction.followup.send("Failed to leave task.", ephemeral=True)
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @volunteer_group.command(name="status", description="See your volunteering status")
    async def status(self, interaction: discord.Interaction):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            user = interaction.user
            data = db.get_user_volunteer_status(str(user.id))
            created = data.get("created", [])
            joined = data.get("joined", [])
            em = embed_utils.base_embed("Your Volunteer Status", color=discord.Color.blue())
            if created:
                for row in created:
                    em.add_field(name=f"Created #{row['id']}", value=f"{row['title']} — {row['status']}", inline=False)
            if joined:
                for row in joined:
                    em.add_field(name=f"Joined #{row['id']}", value=f"{row['title']} — {row['status']}", inline=False)
            if not created and not joined:
                em.description = "No activity yet. Use /volunteer add or /volunteer join."
            await interaction.followup.send(embed=em, ephemeral=True)
        except Exception as e:
            self.logger.error(f"/volunteer status failed: {e}")
            try:
                await interaction.followup.send("Failed to get status.", ephemeral=True)
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @volunteer_group.command(name="remove", description="Remove a volunteer task")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_task(self, interaction: discord.Interaction, task_id: int):
        try:
            # Defer the response since we do database operations
            await interaction.response.defer(ephemeral=True)

            ok = db.remove_volunteer_task(task_id)
            if not ok:
                await interaction.followup.send("Task not found.", ephemeral=True)
                return
            await interaction.followup.send(f"Removed task #{task_id}.")
        except Exception as e:
            self.logger.error(f"/volunteer remove failed: {e}")
            try:
                await interaction.followup.send("Failed to remove task.", ephemeral=True)
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")


async def setup(bot):
    await bot.add_cog(VolunteerCog(bot))