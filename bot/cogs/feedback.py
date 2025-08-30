import discord
from discord import app_commands
from discord.ext import commands
import csv
import os
from datetime import datetime
from bot.utils.embed import success_embed, error_embed, info_embed
from bot.utils.error_handler import (
    error_handler, defer_response, safe_send_response,
    ValidationError, cooldown
)
import logging

class FeedbackModal(discord.ui.Modal, title="Submit Feedback"):
    """Modal for detailed feedback submission."""
    
    category = discord.ui.TextInput(
        label="Category (Optional)",
        placeholder="Bug Report, Feature Request, General Feedback...",
        required=False,
        max_length=50
    )
    
    subject = discord.ui.TextInput(
        label="Subject",
        placeholder="Brief summary of your feedback...",
        required=True,
        max_length=100
    )
    
    message = discord.ui.TextInput(
        label="Detailed Feedback",
        placeholder="Please provide detailed feedback, suggestions, or report issues...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    contact_ok = discord.ui.TextInput(
        label="Contact Permission (yes/no)",
        placeholder="Can we contact you about this feedback? (yes/no)",
        required=False,
        max_length=3,
        default="no"
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate inputs
            subject = self.subject.value.strip()
            message_text = self.message.value.strip()
            category = self.category.value.strip() or "General"
            contact_permission = self.contact_ok.value.strip().lower() in ['yes', 'y', 'true', '1']
            
            if len(subject) < 5:
                embed = error_embed(
                    "Invalid Subject",
                    "Subject must be at least 5 characters long."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if len(message_text) < 10:
                embed = error_embed(
                    "Invalid Message",
                    "Feedback message must be at least 10 characters long."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get the feedback cog to save the feedback
            cog = interaction.client.get_cog('FeedbackCog')
            if cog:
                success = await cog.save_feedback(
                    interaction.user,
                    category,
                    subject,
                    message_text,
                    contact_permission
                )
                
                if success:
                    embed = success_embed(
                        "Feedback Submitted",
                        "Thank you for your feedback! We appreciate your input and will review it carefully."
                    )
                    embed.add_field(
                        name="📋 Submission Details",
                        value=f"**Category:** {category}\n**Subject:** {subject}\n**Contact OK:** {'Yes' if contact_permission else 'No'}",
                        inline=False
                    )
                    embed.add_field(
                        name="🔄 What's Next?",
                        value="• Your feedback has been logged\n• We'll review it within 48 hours\n• Important issues will be prioritized",
                        inline=False
                    )
                else:
                    embed = error_embed(
                        "Submission Failed",
                        "Failed to save your feedback. Please try again later."
                    )
            else:
                embed = error_embed(
                    "System Error",
                    "Feedback system is currently unavailable."
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Feedback modal error: {e}")
            embed = error_embed(
                "Submission Error",
                "An error occurred while submitting your feedback."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class FeedbackView(discord.ui.View):
    """Interactive view for feedback options."""
    
    def __init__(self, timeout: int = 300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label="📝 Detailed Feedback", style=discord.ButtonStyle.primary)
    async def detailed_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FeedbackModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🐛 Quick Bug Report", style=discord.ButtonStyle.danger)
    async def quick_bug_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FeedbackModal()
        modal.category.default = "Bug Report"
        modal.subject.placeholder = "Brief description of the bug..."
        modal.message.placeholder = "Steps to reproduce the bug, what you expected vs what happened..."
        modal.title = "Report a Bug"
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💡 Feature Request", style=discord.ButtonStyle.success)
    async def feature_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FeedbackModal()
        modal.category.default = "Feature Request"
        modal.subject.placeholder = "What feature would you like to see?"
        modal.message.placeholder = "Describe the feature, how it would work, and why it would be useful..."
        modal.title = "Request a Feature"
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⭐ Rate Experience", style=discord.ButtonStyle.secondary)
    async def rate_experience(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FeedbackModal()
        modal.category.default = "Rating"
        modal.subject.placeholder = "Overall experience rating (1-5 stars)"
        modal.message.placeholder = "What did you like? What could be improved? Any specific features you loved or disliked?"
        modal.title = "Rate Your Experience"
        await interaction.response.send_modal(modal)

class FeedbackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.feedback_file = "data/feedback.csv"
        self.feedback_dir = "data"
        
        # Ensure data directory exists
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "User ID", "Username", "Category", 
                    "Subject", "Message", "Contact Permission", "Status"
                ])

    async def save_feedback(self, user: discord.User, category: str, subject: str, 
                          message: str, contact_permission: bool) -> bool:
        """Save feedback to CSV file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.feedback_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    user.id,
                    f"{user.name}",
                    category,
                    subject,
                    message,
                    "Yes" if contact_permission else "No",
                    "New"
                ])
            
            self.logger.info(f"Feedback saved: {category} from {user.name} ({user.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save feedback: {e}")
            return False

    @app_commands.command(
        name="feedback",
        description="Submit feedback, bug reports, or feature requests"
    )
    @app_commands.describe(
        message="Quick feedback message (optional - use buttons for detailed feedback)"
    )
    @error_handler("feedback")
    @cooldown(60)  # 1 minute cooldown to prevent spam
    async def feedback_command(
        self,
        interaction: discord.Interaction,
        message: str = None
    ):
        if message:
            # Quick feedback submission
            await defer_response(interaction, ephemeral=True)
            
            message = message.strip()
            if len(message) < 10:
                raise ValidationError("Feedback message must be at least 10 characters long")
            
            if len(message) > 500:
                raise ValidationError("Quick feedback is limited to 500 characters. Use the detailed feedback option for longer messages.")
            
            # Save quick feedback
            success = await self.save_feedback(
                interaction.user,
                "Quick Feedback",
                "Quick feedback via command",
                message,
                False
            )
            
            if success:
                embed = success_embed(
                    "Feedback Submitted",
                    "Thank you for your quick feedback! We appreciate your input."
                )
                embed.add_field(
                    name="💡 Need More Options?",
                    value="Use `/feedback` without a message to access detailed feedback forms, bug reports, and feature requests.",
                    inline=False
                )
            else:
                embed = error_embed(
                    "Submission Failed",
                    "Failed to save your feedback. Please try again later."
                )
            
            await safe_send_response(interaction, embed=embed, ephemeral=True)
        else:
            # Show interactive feedback options
            embed = info_embed(
                "📢 Submit Feedback",
                "Help us improve by sharing your thoughts, reporting bugs, or suggesting new features!"
            )
            
            embed.add_field(
                name="📝 Feedback Options",
                value="• **Detailed Feedback** - Comprehensive feedback with categories\n• **Bug Report** - Report issues or problems\n• **Feature Request** - Suggest new features\n• **Rate Experience** - Share your overall experience",
                inline=False
            )
            
            embed.add_field(
                name="🔒 Privacy",
                value="• All feedback is reviewed by our team\n• You can choose whether we can contact you\n• Your Discord ID is logged for context only",
                inline=False
            )
            
            embed.add_field(
                name="⚡ Quick Tip",
                value="For quick feedback, use `/feedback <your message>`",
                inline=False
            )
            
            view = FeedbackView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(
        name="feedback-stats",
        description="View feedback statistics (admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @error_handler("feedback-stats")
    async def feedback_stats(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        try:
            if not os.path.exists(self.feedback_file):
                embed = info_embed(
                    "No Feedback Data",
                    "No feedback has been submitted yet."
                )
                await safe_send_response(interaction, embed=embed, ephemeral=True)
                return
            
            # Read and analyze feedback data
            feedback_data = []
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                feedback_data = list(reader)
            
            if not feedback_data:
                embed = info_embed(
                    "No Feedback Data",
                    "No feedback entries found in the database."
                )
                await safe_send_response(interaction, embed=embed, ephemeral=True)
                return
            
            # Calculate statistics
            total_feedback = len(feedback_data)
            categories = {}
            recent_feedback = 0
            contact_ok_count = 0
            
            # Get date 7 days ago
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            
            for entry in feedback_data:
                # Count categories
                category = entry.get('Category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Count recent feedback
                try:
                    entry_date = datetime.strptime(entry['Timestamp'], "%Y-%m-%d %H:%M:%S")
                    if entry_date >= week_ago:
                        recent_feedback += 1
                except:
                    pass
                
                # Count contact permissions
                if entry.get('Contact Permission', '').lower() == 'yes':
                    contact_ok_count += 1
            
            # Create statistics embed
            embed = info_embed(
                "📊 Feedback Statistics",
                f"Analysis of **{total_feedback}** feedback submissions"
            )
            
            embed.add_field(
                name="📈 Recent Activity",
                value=f"**{recent_feedback}** submissions in the last 7 days",
                inline=True
            )
            
            embed.add_field(
                name="📞 Contact Permissions",
                value=f"**{contact_ok_count}** users OK with contact ({contact_ok_count/total_feedback*100:.1f}%)",
                inline=True
            )
            
            embed.add_field(
                name="📋 Top Categories",
                value="\n".join([f"**{cat}:** {count}" for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]]),
                inline=False
            )
            
            # Recent feedback preview
            recent_entries = sorted(feedback_data, key=lambda x: x['Timestamp'], reverse=True)[:3]
            if recent_entries:
                recent_text = []
                for entry in recent_entries:
                    timestamp = entry['Timestamp']
                    category = entry.get('Category', 'Unknown')
                    subject = entry.get('Subject', 'No subject')[:30]
                    recent_text.append(f"**{timestamp}** - {category}: {subject}...")
                
                embed.add_field(
                    name="🕐 Recent Submissions",
                    value="\n".join(recent_text),
                    inline=False
                )
            
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            
        except Exception as e:
            self.logger.error(f"Feedback stats error: {e}")
            embed = error_embed(
                "Stats Error",
                "Failed to generate feedback statistics."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(FeedbackCog(bot))