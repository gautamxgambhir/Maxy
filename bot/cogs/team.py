import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils.embed import (
    team_info_embed, success_embed, error_embed, info_embed, 
    confirmation_embed, ConfirmationView
)
from bot.utils.error_handler import (
    error_handler, defer_response, safe_send_response,
    ProfileNotFoundError, TeamNotFoundError, ValidationError, DatabaseError,
    validate_profile_exists, validate_team_membership,
    validate_team_ownership, cooldown
)
import logging

class TeamCreationModal(discord.ui.Modal, title="🏆 Create Your Team"):
    """Modal for team creation with comprehensive information."""
    
    def __init__(self):
        super().__init__()
    
    team_name = discord.ui.TextInput(
        label="Team Name",
        placeholder="Enter your team name (e.g., CodeCrafters, Innovation Squad)",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    team_description = discord.ui.TextInput(
        label="Team Description",
        placeholder="Describe your team's focus, goals, or what you're looking for...",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    project_idea = discord.ui.TextInput(
        label="Project Idea (Optional)",
        placeholder="Brief description of your project idea or area of interest...",
        required=False,
        max_length=300,
        style=discord.TextStyle.paragraph
    )
    
    looking_for = discord.ui.TextInput(
        label="Looking For (Optional)",
        placeholder="What skills or team members are you looking for? (e.g., Designer, Backend Developer)",
        required=False,
        max_length=200,
        style=discord.TextStyle.short
    )
    
    contact_info = discord.ui.TextInput(
        label="Contact Info (Optional)",
        placeholder="How should others contact you? (Discord, email, etc.)",
        required=False,
        max_length=100,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle team creation submission."""
        try:
            # Check if user already has a profile
            discord_id = str(interaction.user.id)
            profile = db.get_profile(discord_id)
            if not profile:
                await interaction.response.send_message(
                    "❌ You need to create a profile first! Use `/register-profile` to get started.",
                    ephemeral=True
                )
                return
            
            # Check if user is already in a team
            existing_team = db.get_team_by_member(discord_id)
            if existing_team:
                await interaction.response.send_message(
                    "❌ You're already in a team! Leave your current team first to create a new one.",
                    ephemeral=True
                )
                return
            
            # Create team
            try:
                team_id, team_code = db.create_team(
                    self.team_name.value,
                    discord_id,
                    interaction.user.name
                )
            except Exception as e:
                await interaction.response.send_message(
                    "❌ Failed to create team. Please try again.",
                    ephemeral=True
                )
                return
            
            # Create success response
            embed = success_embed(
                "🏆 Team Created Successfully!",
                f"**Team:** {self.team_name.value}\n**Code:** `{team_code}`"
            )
            
            if self.team_description.value:
                embed.add_field(
                    name="📝 Description",
                    value=self.team_description.value,
                    inline=False
                )
            
            if self.project_idea.value:
                embed.add_field(
                    name="💡 Project Idea",
                    value=self.project_idea.value,
                    inline=False
                )
            
            if self.looking_for.value:
                embed.add_field(
                    name="🔍 Looking For",
                    value=self.looking_for.value,
                    inline=True
                )
            
            if self.contact_info.value:
                embed.add_field(
                    name="📞 Contact",
                    value=self.contact_info.value,
                    inline=True
                )
            
            embed.add_field(
                name="🎯 Next Steps",
                value="• Share your team code with others\n• Use the buttons below to manage your team\n• Invite members with `/join-team`",
                inline=False
            )
            
            # Get team data for the view
            team_data = db.get_team_by_member(discord_id)
            view = TeamManagementView(team_data, discord_id)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating team: {str(e)}",
                ephemeral=True
            )

class TeamManagementView(discord.ui.View):
    """Interactive view for team management actions."""
    
    def __init__(self, team_data: dict, user_id: str, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.team_data = team_data
        self.user_id = user_id
        self.is_owner = team_data.get('owner_id') == user_id
        
        # Disable owner-only buttons for non-owners
        if not self.is_owner:
            self.transfer_ownership.disabled = True
            self.delete_team.disabled = True
    
    @discord.ui.button(label="📋 View Members", style=discord.ButtonStyle.primary)
    async def view_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            members = db.get_team_members(self.team_data['id'])
            
            embed = info_embed(
                f"👥 {self.team_data['name']} - Members",
                f"**Team Code:** `{self.team_data['code']}`"
            )
            
            if members:
                member_list = []
                for i, member in enumerate(members, 1):
                    role = "👑 Owner" if member['discord_id'] == self.team_data['owner_id'] else f"{i}. Member"
                    join_date = member['joined_at']
                    if hasattr(join_date, 'strftime'):
                        date_str = join_date.strftime("%b %d, %Y")
                    else:
                        date_str = str(join_date)
                    
                    member_list.append(f"{role} - {member['discord_username']} (joined {date_str})")
                
                embed.add_field(
                    name=f"Members ({len(members)})",
                    value="\n".join(member_list),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Members",
                    value="No members found",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"View members error: {e}")
            await interaction.response.send_message(
                "❌ Failed to load team members.", ephemeral=True
            )
    
    @discord.ui.button(label="🔗 Share Invite", style=discord.ButtonStyle.success)
    async def share_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = success_embed(
            "Team Invite Code",
            f"Share this code with others to invite them to your team!"
        )
        embed.add_field(
            name="📋 Invite Code",
            value=f"```{self.team_data['code']}```",
            inline=False
        )
        embed.add_field(
            name="📝 Instructions for New Members",
            value=f"1. Use the command `/join-team {self.team_data['code']}`\n2. Make sure they have a profile first (`/register-profile`)",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🚪 Leave Team", style=discord.ButtonStyle.danger)
    async def leave_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ You can only leave your own team!", ephemeral=True
            )
            return
        
        if self.is_owner:
            embed = error_embed(
                "Cannot Leave Team",
                "Team owners cannot leave their team.",
                "Transfer ownership first with `/transfer-team-ownership` or delete the team."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = confirmation_embed(
            "Leave Team",
            f"Are you sure you want to leave **{self.team_data['name']}**?",
            "You'll need a new invite code to rejoin later."
        )
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                db.remove_team_member(self.user_id)
                db.delete_team_if_empty(self.team_data['id'])
                
                embed = success_embed(
                    "Left Team",
                    f"You've successfully left **{self.team_data['name']}**."
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Leave team error: {e}")
                embed = error_embed(
                    "Failed to Leave",
                    "An error occurred while leaving the team."
                )
                await interaction.edit_original_response(embed=embed, view=None)
    
    @discord.ui.button(label="👑 Transfer Ownership", style=discord.ButtonStyle.secondary)
    async def transfer_ownership(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner:
            await interaction.response.send_message(
                "❌ Only team owners can transfer ownership!", ephemeral=True
            )
            return
        
        modal = TransferOwnershipModal(self.team_data['id'])
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🗑️ Delete Team", style=discord.ButtonStyle.danger)
    async def delete_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner:
            await interaction.response.send_message(
                "❌ Only team owners can delete teams!", ephemeral=True
            )
            return
        
        embed = confirmation_embed(
            "Delete Team",
            f"Are you sure you want to permanently delete **{self.team_data['name']}**?",
            "⚠️ This will remove all team members and cannot be undone!"
        )
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                db.delete_team(self.team_data['id'])
                
                embed = success_embed(
                    "Team Deleted",
                    f"**{self.team_data['name']}** has been permanently deleted."
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Delete team error: {e}")
                embed = error_embed(
                    "Deletion Failed",
                    "An error occurred while deleting the team."
                )
                await interaction.edit_original_response(embed=embed, view=None)

class TransferOwnershipModal(discord.ui.Modal, title="Transfer Team Ownership"):
    """Modal for transferring team ownership."""
    
    def __init__(self, team_id: int):
        super().__init__()
        self.team_id = team_id
    
    new_owner = discord.ui.TextInput(
        label="New Owner Username",
        placeholder="Enter the Discord username of the new owner...",
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Find the user by username
            guild = interaction.guild
            new_owner_member = None
            
            # Try to find member by username
            for member in guild.members:
                if member.name.lower() == self.new_owner.value.lower():
                    new_owner_member = member
                    break
            
            if not new_owner_member:
                embed = error_embed(
                    "User Not Found",
                    f"Could not find a user with username: {self.new_owner.value}",
                    "Make sure the username is correct and the user is in this server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            new_owner_id = str(new_owner_member.id)
            
            # Check if new owner is a team member
            members = db.get_team_members(self.team_id)
            if not any(m['discord_id'] == new_owner_id for m in members):
                embed = error_embed(
                    "Not a Team Member",
                    f"{new_owner_member.mention} is not a member of this team.",
                    "Only current team members can become owners."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Transfer ownership
            db.transfer_team_ownership(self.team_id, new_owner_id)
            
            embed = success_embed(
                "Ownership Transferred",
                f"Team ownership has been transferred to {new_owner_member.mention}!"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Transfer ownership error: {e}")
            embed = error_embed(
                "Transfer Failed",
                "An error occurred while transferring ownership."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class TeamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(
        name="create-team", 
        description="Create a new team for hackathons and collaborations"
    )
    @error_handler("create-team")
    @validate_profile_exists
    @cooldown(30)  # 30 second cooldown to prevent spam
    async def create_team(self, interaction: discord.Interaction):
        """Open team creation modal."""
        # Check if user is already in a team
        current_team = db.get_team_by_member(str(interaction.user.id))
        if current_team:
            embed = error_embed(
                "Already in Team",
                f"You're already in team **{current_team['name']}**!",
                "Leave your current team first with `/leave-team` or use the team management buttons."
            )
            
            # Show current team info with management options
            team_data = {
                'name': current_team['name'],
                'code': current_team['code'],
                'owner': current_team['owner_id'],
                'members': [m['discord_username'] for m in db.get_team_members(current_team['id'])]
            }
            
            team_embed = team_info_embed(team_data)
            view = TeamManagementView(current_team, str(interaction.user.id))
            
            await interaction.response.send_message(
                embed=team_embed,
                view=view,
                ephemeral=True
            )
            return
        
        # Open team creation modal
        modal = TeamCreationModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="join-team", 
        description="Join a team using an invite code"
    )
    @app_commands.describe(
        code="Team invitation code"
    )
    @error_handler("join-team")
    @validate_profile_exists
    @cooldown(5)
    async def join_team(self, interaction: discord.Interaction, code: str):
        await defer_response(interaction, ephemeral=True)
        
        discord_id = str(interaction.user.id)
        discord_username = interaction.user.name
        
        # Check if already in a team
        current_team = db.get_team_by_member(discord_id)
        if current_team:
            embed = error_embed(
                "Already in Team",
                f"You're already in team **{current_team['name']}**!",
                "Leave your current team first if you want to join a different one."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        # Find team by code
        team = db.get_team_by_code(code.strip().upper())
        if not team:
            embed = error_embed(
                "Invalid Team Code",
                f"No team found with code: `{code}`",
                "Double-check the code and try again. Team codes are case-insensitive."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        try:
            db.add_team_member(team["id"], discord_id, discord_username)
        except Exception as e:
            self.logger.error(f"Join team error: {e}")
            embed = error_embed(
                "Failed to Join",
                "An error occurred while joining the team.",
                "The team might be full or there was a database error. Try again later."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        # Get updated team info
        members = db.get_team_members(team["id"])
        member_names = [m["discord_username"] for m in members]
        
        team_data = {
            'name': team['name'],
            'code': team['code'],
            'owner': team['owner_id'],
            'members': member_names
        }
        
        embed = team_info_embed(team_data)
        embed.title = f"✅ Welcome to {team['name']}!"
        embed.add_field(
            name="🎉 You're In!",
            value="You've successfully joined the team. Use the buttons below to manage your team membership.",
            inline=False
        )
        
        view = TeamManagementView(team, discord_id)
        await safe_send_response(
            interaction,
            embed=embed,
            view=view,
            ephemeral=True
        )
        
        self.logger.info(f"{discord_username} joined team {team['name']}")

    @app_commands.command(
        name="view-team", 
        description="View your current team information and manage it"
    )
    @error_handler("view-team")
    @validate_team_membership
    async def view_team(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        discord_id = str(interaction.user.id)
        team = db.get_team_by_member(discord_id)
        
        # Get team members
        members = db.get_team_members(team["id"])
        member_names = [m["discord_username"] for m in members]
        
        # Get owner profile for display name
        owner_profile = db.get_profile(team["owner_id"])
        owner_name = owner_profile["name"] if owner_profile else team["owner_id"]
        
        team_data = {
            'name': team['name'],
            'code': team['code'],
            'owner': owner_name,
            'members': member_names
        }
        
        embed = team_info_embed(team_data)
        embed.add_field(
            name="🛠️ Team Management",
            value="Use the buttons below to manage your team, view members, or share the invite code.",
            inline=False
        )
        
        view = TeamManagementView(team, discord_id)
        await safe_send_response(
            interaction,
            embed=embed,
            view=view,
            ephemeral=True
        )

    @app_commands.command(
        name="leave-team", 
        description="Leave your current team"
    )
    @error_handler("leave-team")
    @validate_team_membership
    @cooldown(10)
    async def leave_team(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        discord_id = str(interaction.user.id)
        team = db.get_team_by_member(discord_id)
        
        # Check if user is team owner
        if team["owner_id"] == discord_id:
            embed = error_embed(
                "Cannot Leave Team",
                "Team owners cannot leave their team.",
                "Transfer ownership first with `/transfer-team-ownership` or delete the team with `/delete-team`."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        embed = confirmation_embed(
            "Leave Team",
            f"Are you sure you want to leave **{team['name']}**?",
            "You'll need a new invite code to rejoin later."
        )
        
        view = ConfirmationView()
        await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                db.remove_team_member(discord_id)
                db.delete_team_if_empty(team["id"])
                
                embed = success_embed(
                    "Left Team",
                    f"You've successfully left **{team['name']}**.",
                    "You can join a new team anytime with `/join-team`."
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
                self.logger.info(f"{interaction.user.name} left team {team['name']}")
                
            except Exception as e:
                self.logger.error(f"Leave team error: {e}")
                embed = error_embed(
                    "Failed to Leave",
                    "An error occurred while leaving the team."
                )
                await interaction.edit_original_response(embed=embed, view=None)

    @app_commands.command(
        name="delete-team", 
        description="Delete your team (owners only)"
    )
    @error_handler("delete-team")
    @validate_team_ownership
    @cooldown(60)  # 1 minute cooldown for destructive action
    async def delete_team(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        discord_id = str(interaction.user.id)
        team = db.get_team_by_member(discord_id)
        
        embed = confirmation_embed(
            "Delete Team",
            f"Are you sure you want to permanently delete **{team['name']}**?",
            "⚠️ This will remove all team members and cannot be undone!"
        )
        
        view = ConfirmationView()
        await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                db.delete_team(team["id"])
                
                embed = success_embed(
                    "Team Deleted",
                    f"**{team['name']}** has been permanently deleted."
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
                self.logger.info(f"Team deleted: {team['name']} by {interaction.user.name}")
                
            except Exception as e:
                self.logger.error(f"Delete team error: {e}")
                embed = error_embed(
                    "Deletion Failed",
                    "An error occurred while deleting the team."
                )
                await interaction.edit_original_response(embed=embed, view=None)

    @app_commands.command(
        name="transfer-team-ownership", 
        description="Transfer team ownership to another member"
    )
    @app_commands.describe(
        new_owner="The team member to transfer ownership to"
    )
    @error_handler("transfer-team-ownership")
    @validate_team_ownership
    @cooldown(30)
    async def transfer_ownership(
        self, 
        interaction: discord.Interaction, 
        new_owner: discord.Member
    ):
        await defer_response(interaction, ephemeral=True)
        
        discord_id = str(interaction.user.id)
        new_owner_id = str(new_owner.id)
        team = db.get_team_by_member(discord_id)
        
        # Check if new owner is a team member
        members = db.get_team_members(team["id"])
        if not any(m["discord_id"] == new_owner_id for m in members):
            embed = error_embed(
                "Not a Team Member",
                f"{new_owner.mention} is not a member of your team.",
                "Only current team members can become owners."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        embed = confirmation_embed(
            "Transfer Ownership",
            f"Are you sure you want to transfer ownership of **{team['name']}** to {new_owner.mention}?",
            "You will no longer be the team owner after this transfer."
        )
        
        view = ConfirmationView()
        await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                db.transfer_team_ownership(team["id"], new_owner_id)
                
                embed = success_embed(
                    "Ownership Transferred",
                    f"Team ownership has been transferred to {new_owner.mention}!"
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
                self.logger.info(f"Ownership transferred in {team['name']} to {new_owner.name}")
                
            except Exception as e:
                self.logger.error(f"Transfer ownership error: {e}")
                embed = error_embed(
                    "Transfer Failed",
                    "An error occurred while transferring ownership."
                )
                await interaction.edit_original_response(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(TeamCog(bot))
