import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils import validation
from bot.utils.embed import profile_embed, success_embed, error_embed, info_embed, ConfirmationView
from bot.utils.error_handler import (
    error_handler, defer_response, safe_send_response,
    ProfileNotFoundError, ValidationError, DatabaseError, cooldown
)
import logging

class ProfileRegistrationModal(discord.ui.Modal, title="👤 Create Your Profile"):
    """Comprehensive modal for profile registration."""
    
    def __init__(self):
        super().__init__()
    
    name = discord.ui.TextInput(
        label="Full Name",
        placeholder="Enter your full name (e.g., John Doe)",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    skills = discord.ui.TextInput(
        label="Skills & Expertise",
        placeholder="Enter your skills separated by commas (e.g., Python, React, UI/UX, Project Management)",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    interests = discord.ui.TextInput(
        label="Interests & Goals",
        placeholder="What are you passionate about? (e.g., AI, Sustainability, Gaming, Social Impact)",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    github = discord.ui.TextInput(
        label="GitHub Profile (Optional)",
        placeholder="Your GitHub username or profile URL",
        required=False,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    portfolio = discord.ui.TextInput(
        label="Portfolio/Website (Optional)",
        placeholder="Your portfolio website or LinkedIn profile",
        required=False,
        max_length=200,
        style=discord.TextStyle.short
    )
    
    bio = discord.ui.TextInput(
        label="Bio (Optional)",
        placeholder="Tell us about yourself in a few sentences...",
        required=False,
        max_length=300,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle profile registration submission."""
        try:
            # Validate inputs
            try:
                validated_name = validation.validate_name(self.name.value)
                validated_skills = validation.validate_skills(self.skills.value) if self.skills.value else ""
                validated_interests = validation.validate_interests(self.interests.value) if self.interests.value else ""
            except ValueError as e:
                await interaction.response.send_message(
                    f"❌ Validation error: {str(e)}\nPlease check your input format and try again.",
                    ephemeral=True
                )
                return
            
            discord_id = str(interaction.user.id)
            discord_username = interaction.user.name
            
            # Check if profile already exists
            existing_profile = db.get_profile(discord_id)
            if existing_profile:
                embed = info_embed(
                    "Profile Already Exists",
                    "You already have a profile! Use `/edit-profile` to update it."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create profile
            try:
                db.upsert_profile(
                    discord_id,
                    discord_username,
                    validated_name,
                    validated_skills,
                    validated_interests
                )
            except Exception as e:
                await interaction.response.send_message(
                    "❌ Database error creating profile. Please try again.",
                    ephemeral=True
                )
                return
            
            # Create success response
            profile_data = {
                'name': validated_name,
                'discord_username': discord_username,
                'skills': validated_skills,
                'interests': validated_interests
            }
            
            embed = profile_embed(profile_data)
            embed.title = "✅ Profile Created Successfully!"
            embed.add_field(
                name="🎉 Welcome to Maximally!",
                value="Your profile helps others find teammates with complementary skills. Use `/edit-profile` to update it anytime.",
                inline=False
            )
            
            if self.github.value:
                embed.add_field(name="🔗 GitHub", value=self.github.value, inline=True)
            if self.portfolio.value:
                embed.add_field(name="🌐 Portfolio", value=self.portfolio.value, inline=True)
            if self.bio.value:
                embed.add_field(name="📝 Bio", value=self.bio.value, inline=False)
            
            view = ProfileActionView(discord_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating profile: {str(e)}",
                ephemeral=True
            )

class ProfileEditModal(discord.ui.Modal, title="✏️ Edit Your Profile"):
    """Modal for editing profile information."""
    
    def __init__(self, current_profile):
        super().__init__()
        self.current_profile = current_profile
    
    name = discord.ui.TextInput(
        label="Full Name",
        default=current_profile.get('name', ''),
        placeholder="Enter your full name",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    skills = discord.ui.TextInput(
        label="Skills & Expertise",
        default=current_profile.get('skills', ''),
        placeholder="Enter your skills separated by commas",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    interests = discord.ui.TextInput(
        label="Interests & Goals",
        default=current_profile.get('interests', ''),
        placeholder="What are you passionate about?",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    bio = discord.ui.TextInput(
        label="Bio (Optional)",
        default=current_profile.get('bio', ''),
        placeholder="Tell us about yourself...",
        required=False,
        max_length=300,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle profile edit submission."""
        try:
            # Validate inputs
            try:
                validated_name = validation.validate_name(self.name.value)
                validated_skills = validation.validate_skills(self.skills.value) if self.skills.value else ""
                validated_interests = validation.validate_interests(self.interests.value) if self.interests.value else ""
            except ValueError as e:
                await interaction.response.send_message(
                    f"❌ Validation error: {str(e)}\nPlease check your input format and try again.",
                    ephemeral=True
                )
                return
            
            discord_id = str(interaction.user.id)
            discord_username = interaction.user.name
            
            # Update profile
            try:
                db.upsert_profile(
                    discord_id,
                    discord_username,
                    validated_name,
                    validated_skills,
                    validated_interests
                )
            except Exception as e:
                await interaction.response.send_message(
                    "❌ Database error updating profile. Please try again.",
                    ephemeral=True
                )
                return
            
            # Create success response
            profile_data = {
                'name': validated_name,
                'discord_username': discord_username,
                'skills': validated_skills,
                'interests': validated_interests
            }
            
            embed = profile_embed(profile_data)
            embed.title = "✅ Profile Updated Successfully!"
            embed.add_field(
                name="🔄 Changes Saved",
                value="Your profile has been updated with the new information.",
                inline=False
            )
            
            view = ProfileActionView(discord_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating profile: {str(e)}",
                ephemeral=True
            )

class ProfileActionView(discord.ui.View):
    """Interactive view for profile actions."""
    
    def __init__(self, user_id: str, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.user_id = user_id
    
    @discord.ui.button(label="✏️ Edit Profile", style=discord.ButtonStyle.primary)
    async def edit_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ You can only edit your own profile!", ephemeral=True
            )
            return
        
        # Get current profile data
        current_profile = db.get_profile(self.user_id)
        if not current_profile:
            await interaction.response.send_message(
                "❌ Profile not found!", ephemeral=True
            )
            return
        
        modal = ProfileEditModal(current_profile)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔍 Find Similar", style=discord.ButtonStyle.secondary)
    async def find_similar(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            profile = db.get_profile(self.user_id)
            if not profile:
                await interaction.response.send_message(
                    "❌ Profile not found!", ephemeral=True
                )
                return
            
            # Search for similar profiles based on skills and interests
            results = db.search_profiles(
                skills=profile.get('skills', ''),
                interests=profile.get('interests', ''),
                limit=5
            )
            
            # Remove self from results
            results = [r for r in results if r['discord_id'] != self.user_id]
            
            if not results:
                embed = info_embed(
                    "No Similar Profiles Found",
                    "Try adding more skills or interests to find people with similar backgrounds!"
                )
            else:
                from bot.utils.embed import search_results_embed
                embed = search_results_embed(results)
                embed.title = "🔍 People Similar to You"
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Find similar error: {e}")
            await interaction.response.send_message(
                "❌ Failed to find similar profiles.", ephemeral=True
            )
    
    @discord.ui.button(label="🗑️ Delete Profile", style=discord.ButtonStyle.danger)
    async def delete_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ You can only delete your own profile!", ephemeral=True
            )
            return
        
        from bot.utils.embed import confirmation_embed
        embed = confirmation_embed(
            "Delete Profile",
            "Are you sure you want to delete your profile? This action cannot be undone.",
            "⚠️ This will permanently remove all your profile information."
        )
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                # Delete profile from database
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    query = "DELETE FROM profiles WHERE discord_id = %s" if db.mode == "postgres" else "DELETE FROM profiles WHERE discord_id = ?"
                    cursor.execute(query, (self.user_id,))
                    if db.mode == "sqlite":
                        conn.commit()
                
                embed = success_embed(
                    "Profile Deleted",
                    "Your profile has been permanently deleted."
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Profile deletion error: {e}")
                embed = error_embed(
                    "Deletion Failed",
                    "Failed to delete your profile. Please try again later."
                )
                await interaction.edit_original_response(embed=embed, view=None)

class ProfileEditModal(discord.ui.Modal, title="Edit Your Profile"):
    """Modal for editing profile information."""
    
    name = discord.ui.TextInput(
        label="Full Name",
        placeholder="Enter your full name...",
        required=True,
        max_length=100
    )
    
    skills = discord.ui.TextInput(
        label="Skills (comma separated)",
        placeholder="Python, JavaScript, UI/UX Design...",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    interests = discord.ui.TextInput(
        label="Interests (comma separated)",
        placeholder="Machine Learning, Web Development, Gaming...",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate inputs
            validated_name = validation.validate_name(self.name.value)
            validated_skills = validation.validate_skills(self.skills.value)
            validated_interests = validation.validate_interests(self.interests.value)
            
            discord_id = str(interaction.user.id)
            discord_username = interaction.user.name
            
            # Update profile
            db.upsert_profile(
                discord_id,
                discord_username,
                validated_name,
                validated_skills,
                validated_interests
            )
            
            # Create updated profile embed
            profile_data = {
                'name': validated_name,
                'discord_username': discord_username,
                'skills': validated_skills,
                'interests': validated_interests
            }
            
            embed = profile_embed(profile_data)
            embed.title = "✅ Profile Updated Successfully!"
            
            view = ProfileActionView(discord_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except ValueError as e:
            embed = error_embed(
                "Validation Error",
                str(e),
                "Please check your input and try again."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.getLogger(__name__).error(f"Profile edit error: {e}")
            embed = error_embed(
                "Update Failed",
                "Failed to update your profile. Please try again later."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(
        name="register-profile",
        description="Create your profile to connect with other hackathon participants"
    )
    @error_handler("register-profile")
    @cooldown(10)  # 10 second cooldown to prevent spam
    async def register_profile(self, interaction: discord.Interaction):
        """Open profile registration modal."""
        # Check if profile already exists
        existing_profile = db.get_profile(str(interaction.user.id))
        if existing_profile:
            embed = info_embed(
                "Profile Already Exists",
                "You already have a profile! Use the buttons below to manage it."
            )
            
            profile_data = {
                'name': existing_profile['name'],
                'discord_username': existing_profile['discord_username'],
                'skills': existing_profile['skills'],
                'interests': existing_profile['interests']
            }
            
            profile_embed_obj = profile_embed(profile_data)
            view = ProfileActionView(str(interaction.user.id))
            
            await interaction.response.send_message(
                embed=profile_embed_obj,
                view=view,
                ephemeral=True
            )
            return
        
        # Open profile registration modal
        modal = ProfileRegistrationModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="edit-profile",
        description="Update your profile information"
    )
    @error_handler("edit-profile")
    @cooldown(5)
    async def edit_profile(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        # Check if profile exists
        profile = db.get_profile(str(interaction.user.id))
        if not profile:
            raise ProfileNotFoundError()
        
        # Show edit modal
        modal = ProfileEditModal()
        
        # Pre-fill modal with current values
        modal.name.default = profile['name']
        modal.skills.default = profile.get('skills', '')
        modal.interests.default = profile.get('interests', '')
        
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name="view-profile",
        description="View your profile or someone else's profile"
    )
    @app_commands.describe(
        user="The user whose profile you want to view (optional, defaults to yourself)"
    )
    @error_handler("view-profile")
    async def view_profile(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None
    ):
        await defer_response(interaction, ephemeral=True)
        
        target_user = user or interaction.user
        discord_id = str(target_user.id)
        
        profile = db.get_profile(discord_id)
        if not profile:
            if target_user == interaction.user:
                raise ProfileNotFoundError()
            else:
                embed = info_embed(
                    "Profile Not Found",
                    f"{target_user.mention} hasn't created a profile yet.",
                    "Encourage them to use `/register-profile` to join the community!"
                )
                await safe_send_response(interaction, embed=embed, ephemeral=True)
                return
        
        profile_data = {
            'name': profile['name'],
            'discord_username': profile['discord_username'],
            'skills': profile['skills'],
            'interests': profile['interests']
        }
        
        embed = profile_embed(profile_data)
        
        # Add action buttons only for own profile
        view = None
        if target_user == interaction.user:
            view = ProfileActionView(discord_id)
            embed.add_field(
                name="💡 Profile Tips",
                value="• Keep your skills updated\n• Add specific interests\n• Use the buttons below to manage your profile",
                inline=False
            )
        else:
            embed.add_field(
                name="🤝 Connect",
                value=f"Reach out to {target_user.mention} if you share similar interests or need their skills!",
                inline=False
            )
        
        await safe_send_response(
            interaction,
            embed=embed,
            view=view,
            ephemeral=True
        )
        
        self.logger.info(f"Profile viewed: {profile['discord_username']} by {interaction.user.name}")

    @app_commands.command(
        name="profile-stats",
        description="View statistics about profiles in the server"
    )
    @error_handler("profile-stats")
    async def profile_stats(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total profiles
                cursor.execute("SELECT COUNT(*) FROM profiles")
                total_profiles = cursor.fetchone()[0] if db.mode == "sqlite" else cursor.fetchone()["count"]
                
                # Get profiles with skills
                cursor.execute("SELECT COUNT(*) FROM profiles WHERE skills IS NOT NULL AND skills != ''")
                profiles_with_skills = cursor.fetchone()[0] if db.mode == "sqlite" else cursor.fetchone()["count"]
                
                # Get profiles with interests
                cursor.execute("SELECT COUNT(*) FROM profiles WHERE interests IS NOT NULL AND interests != ''")
                profiles_with_interests = cursor.fetchone()[0] if db.mode == "sqlite" else cursor.fetchone()["count"]
                
                # Get most common skills (simplified)
                cursor.execute("SELECT skills FROM profiles WHERE skills IS NOT NULL AND skills != '' LIMIT 100")
                skills_data = cursor.fetchall()
                
                skill_counts = {}
                for row in skills_data:
                    skills = row[0] if db.mode == "sqlite" else row["skills"]
                    if skills:
                        for skill in skills.split(','):
                            skill = skill.strip().lower()
                            if skill:
                                skill_counts[skill] = skill_counts.get(skill, 0) + 1
                
                top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        except Exception as e:
            self.logger.error(f"Stats query error: {e}")
            raise DatabaseError()
        
        embed = info_embed(
            "📊 Profile Statistics",
            f"Community insights for **{interaction.guild.name}**"
        )
        
        embed.add_field(
            name="👥 Total Profiles",
            value=f"```{total_profiles:,} members```",
            inline=True
        )
        
        embed.add_field(
            name="🛠️ With Skills",
            value=f"```{profiles_with_skills:,} profiles```",
            inline=True
        )
        
        embed.add_field(
            name="❤️ With Interests",
            value=f"```{profiles_with_interests:,} profiles```",
            inline=True
        )
        
        if top_skills:
            skills_text = "\n".join([f"{i+1}. {skill.title()} ({count})" for i, (skill, count) in enumerate(top_skills)])
            embed.add_field(
                name="🔥 Popular Skills",
                value=f"```{skills_text}```",
                inline=False
            )
        
        completion_rate = (profiles_with_skills / total_profiles * 100) if total_profiles > 0 else 0
        embed.add_field(
            name="📈 Profile Completion",
            value=f"```{completion_rate:.1f}% have added skills```",
            inline=False
        )
        
        await safe_send_response(interaction, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))