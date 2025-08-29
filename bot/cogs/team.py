import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils.embed import team_info_embed
import logging

class TeamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(name="create-team", description="Create a new team")
    @app_commands.describe(name="Your team name")
    async def create_team(self, interaction: discord.Interaction, name: str):
        try:
            await interaction.response.defer(ephemeral=True)
            profile = db.get_profile(str(interaction.user.id))
            if not profile:
                await interaction.followup.send(
                    "❌ You need to create a profile first using `/register-profile`",
                    ephemeral=True,
                )
                return

            current_team = db.get_team_by_member(str(interaction.user.id))
            if current_team:
                await interaction.followup.send(
                    "❌ You're already in a team! Leave your current team first.",
                    ephemeral=True,
                )
                return

            discord_id = str(interaction.user.id)
            discord_username = (
                f"{interaction.user.name}"
            )

            team_id, code = db.create_team(name, discord_id, discord_username)

            embed = team_info_embed(
                {
                    "name": name,
                    "code": code,
                    "owner": discord_username,
                    "members": [discord_username],
                }
            )

            await interaction.followup.send(
                embed=embed,
                content=f"✅ Team created! Your team code: `{code}`",
                ephemeral=True,
            )
            self.logger.info(f"Team created: {name} by {discord_username}")

        except Exception as e:
            self.logger.error(f"Create team error: {str(e)}")
            await interaction.followup.send(
                "❌ Failed to create team. Please try again later.", ephemeral=True
            )

    @app_commands.command(name="join-team", description="Join a team using a code")
    @app_commands.describe(code="Team invitation code")
    async def join_team(self, interaction: discord.Interaction, code: str):
        try:
            await interaction.response.defer(ephemeral=True)
            profile = db.get_profile(str(interaction.user.id))
            if not profile:
                await interaction.followup.send(
                    "❌ You need to create a profile first using `/register-profile`",
                    ephemeral=True,
                )
                return

            discord_id = str(interaction.user.id)
            discord_username = (
                f"{interaction.user.name}"
            )

            current_team = db.get_team_by_member(discord_id)
            if current_team:
                await interaction.followup.send(
                    "❌ You're already in a team! Leave your current team first.",
                    ephemeral=True,
                )
                return

            team = db.get_team_by_code(code.strip().upper())
            if not team:
                await interaction.followup.send(
                    "❌ Invalid team code. Please check and try again.", ephemeral=True
                )
                return

            db.add_team_member(team["id"], discord_id, discord_username)

            members = db.get_team_members(team["id"])
            member_names = [m["discord_username"] for m in members]

            embed = team_info_embed(
                {
                    "name": team["name"],
                    "code": team["code"],
                    "owner": team["owner_id"],
                    "members": member_names,
                }
            )

            await interaction.followup.send(
                embed=embed,
                content=f"✅ You've joined team **{team['name']}**!",
                ephemeral=True,
            )
            self.logger.info(f"{discord_username} joined team {team['name']}")

        except Exception as e:
            self.logger.error(f"Join team error: {str(e)}")
            await interaction.followup.send(
                "❌ Failed to join team. Please try again later.", ephemeral=True
            )

    @app_commands.command(
        name="view-team", description="View your current team information"
    )
    async def view_team(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            team = db.get_team_by_member(discord_id)

            if not team:
                await interaction.followup.send(
                    "❌ You're not currently in a team.", ephemeral=True
                )
                return

            members = db.get_team_members(team["id"])
            member_names = [m["discord_username"] for m in members]

            owner_profile = db.get_profile(team["owner_id"])
            owner_name = owner_profile["name"] if owner_profile else team["owner_id"]

            embed = team_info_embed(
                {
                    "name": team["name"],
                    "code": team["code"],
                    "owner": owner_name,
                    "members": member_names,
                }
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"View team error: {str(e)}")
            await interaction.followup.send(
                "❌ Failed to retrieve team information.", ephemeral=True
            )

    @app_commands.command(name="leave-team", description="Leave your current team")
    async def leave_team(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            discord_username = f"{interaction.user.name}"

            team = db.get_team_by_member(discord_id)
            if not team:
                await interaction.followup.send(
                    "❌ You're not currently in a team.", ephemeral=True
                )
                return

            if team["owner_id"] == discord_id:
                await interaction.followup.send(
                    "❌ Team owners cannot leave their team. Transfer ownership first or delete the team.",
                    ephemeral=True,
                )
                return
            
            db.remove_team_member(discord_id)

            db.delete_team_if_empty(team["id"])

            await interaction.followup.send(
                f"✅ You've left team **{team['name']}**.", ephemeral=True
            )
            self.logger.info(f"{discord_username} left team {team['name']}")

        except Exception as e:
            self.logger.error(f"Leave team error: {str(e)}")
            await interaction.followup.send(
                "❌ Failed to leave team. Please try again later.", ephemeral=True
            )

    @app_commands.command(name="delete-team", description="Delete your team (owners only)")
    async def delete_team(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            discord_username = interaction.user.name

            team = db.get_team_by_member(discord_id)
            if not team:
                await interaction.followup.send(
                    "❌ You're not currently in a team.", ephemeral=True
                )
                return

            if team["owner_id"] != discord_id:
                await interaction.followup.send(
                    "❌ Only team owners can delete teams.", ephemeral=True
                )
                return

            confirm_embed = discord.Embed(
                title="⚠️ Confirm Team Deletion",
                description=f"Are you sure you want to delete **{team['name']}**? This action is permanent!",
                color=discord.Color.red()
            )
            confirm_embed.set_footer(text="This will remove all team members and cannot be undone")
            
            view = discord.ui.View(timeout=60)
            confirm_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Delete Team")
            cancel_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Cancel")
            
            async def confirm_callback(confirm_interaction):
                if confirm_interaction.user.id != interaction.user.id:
                    await confirm_interaction.response.send_message(
                        "❌ Only the command initiator can confirm deletion.", ephemeral=True
                    )
                    return
                    
                db.delete_team(team["id"])
                
                await confirm_interaction.response.edit_message(
                    content=f"✅ Team **{team['name']}** has been deleted.",
                    embed=None,
                    view=None
                )
                self.logger.info(f"Team deleted: {team['name']} by {discord_username}")
            
            async def cancel_callback(cancel_interaction):
                if cancel_interaction.user.id != interaction.user.id:
                    await cancel_interaction.response.send_message(
                        "❌ Only the command initiator can cancel.", ephemeral=True
                    )
                    return
                    
                await cancel_interaction.response.edit_message(
                    content="❌ Team deletion canceled.",
                    embed=None,
                    view=None
                )
            
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            
            await interaction.followup.send(
                embed=confirm_embed,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            self.logger.error(f"Delete team error: {str(e)}")
            await interaction.followup.send(
                "❌ Failed to delete team. Please try again later.", ephemeral=True
            )

    @app_commands.command(name="transfer-team-ownership", description="Transfer team ownership to another member")
    @app_commands.describe(new_owner="The team member to transfer ownership to")
    async def transfer_ownership(
        self, 
        interaction: discord.Interaction, 
        new_owner: discord.Member
    ):
        try:
            await interaction.response.defer(ephemeral=True)
            discord_id = str(interaction.user.id)
            new_owner_id = str(new_owner.id)
            
            team = db.get_team_by_member(discord_id)
            if not team:
                await interaction.followup.send(
                    "❌ You're not currently in a team.", ephemeral=True
                )
                return

            if team["owner_id"] != discord_id:
                await interaction.followup.send(
                    "❌ Only team owners can transfer ownership.", ephemeral=True
                )
                return
                
            members = db.get_team_members(team["id"])
            new_owner_in_team = any(m["discord_id"] == new_owner_id for m in members)
            
            if not new_owner_in_team:
                await interaction.followup.send(
                    "❌ The new owner must be a current team member.", ephemeral=True
                )
                return
                
            confirm_embed = discord.Embed(
                title="⚠️ Confirm Ownership Transfer",
                description=f"Are you sure you want to transfer ownership of **{team['name']}** to {new_owner.mention}?",
                color=discord.Color.orange()
            )
            confirm_embed.set_footer(text="You will no longer be team owner after this transfer")
            
            view = discord.ui.View(timeout=60)
            confirm_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Transfer Ownership")
            cancel_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Cancel")
            
            async def confirm_callback(confirm_interaction):
                if confirm_interaction.user.id != interaction.user.id:
                    await confirm_interaction.response.send_message(
                        "❌ Only the command initiator can confirm transfer.", ephemeral=True
                    )
                    return
                    
                db.transfer_team_ownership(team["id"], new_owner_id)
                
                members = db.get_team_members(team["id"])
                member_names = [m["discord_username"] for m in members]
                
                new_owner_profile = db.get_profile(new_owner_id)
                new_owner_name = new_owner_profile["name"] if new_owner_profile else new_owner.display_name
                
                embed = team_info_embed({
                    "name": team["name"],
                    "code": team["code"],
                    "owner": new_owner_name,
                    "members": member_names
                })
                
                await confirm_interaction.response.edit_message(
                    content=f"✅ Ownership transferred to {new_owner.mention}!",
                    embed=embed,
                    view=None
                )
                self.logger.info(f"Ownership transferred in {team['name']} to {new_owner.name}")
            
            async def cancel_callback(cancel_interaction):
                if cancel_interaction.user.id != interaction.user.id:
                    await cancel_interaction.response.send_message(
                        "❌ Only the command initiator can cancel.", ephemeral=True
                    )
                    return
                    
                await cancel_interaction.response.edit_message(
                    content="❌ Ownership transfer canceled.",
                    embed=None,
                    view=None
                )
            
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            
            await interaction.followup.send(
                embed=confirm_embed,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            self.logger.error(f"Transfer ownership error: {str(e)}")
            await interaction.followup.send(
                "❌ Failed to transfer ownership. Please try again later.", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(TeamCog(bot))
