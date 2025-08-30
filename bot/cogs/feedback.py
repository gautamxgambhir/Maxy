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

class FeedbackSubmissionModal(discord.ui.Modal, title="📢 Submit Feedback"):
    """Comprehensive modal for feedback submission."""
    
    def __init__(self, feedback_type: str = "general"):
        super().__init__()
        self.feedback_type = feedback_type
    
    feedback_title = discord.ui.TextInput(
        label="Feedback Title",
        placeholder="Brief summary of your feedback (e.g., 'Great team matching feature')",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    feedback_message = discord.ui.TextInput(
        label="Detailed Feedback",
        placeholder="Please provide detailed feedback, suggestions, or describe any issues you encountered...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    category = discord.ui.TextInput(
        label="Category",
        placeholder="What type of feedback is this? (e.g., Feature, Bug, UI/UX, Team Management)",
        required=False,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    priority = discord.ui.TextInput(
        label="Priority Level (Optional)",
        placeholder="How important is this? (Low, Medium, High, Critical)",
        required=False,
        max_length=20,
        style=discord.TextStyle.short
    )
    
    contact_permission = discord.ui.TextInput(
        label="Contact Permission (Optional)",
        placeholder="Can we contact you for follow-up? (Yes/No and preferred method)",
        required=False,
        max_length=100,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle feedback submission."""
        try:
            # Validate inputs
            if not self.feedback_title.value.strip():
                await interaction.response.send_message(
                    "❌ Feedback title is required!",
                    ephemeral=True
                )
                return
            
            if not self.feedback_message.value.strip():
                await interaction.response.send_message(
                    "❌ Feedback message is required!",
                    ephemeral=True
                )
                return
            
            # Get the feedback cog to save the feedback
            cog = interaction.client.get_cog('FeedbackCog')
            if not cog:
                await interaction.response.send_message(
                    "❌ Feedback system not available.",
                    ephemeral=True
                )
                return
            
            # Save feedback
            success = await cog.save_feedback(
                interaction.user,
                self.feedback_title.value.strip(),
                self.feedback_type,
                self.feedback_message.value.strip(),
                True  # Detailed feedback
            )
            
            if success:
                embed = success_embed(
                    "✅ Feedback Submitted Successfully!",
                    "Thank you for your detailed feedback! We appreciate your input."
                )
                
                embed.add_field(
                    name="📝 Feedback Details",
                    value=f"**Title:** {self.feedback_title.value.strip()}\n**Type:** {self.feedback_type.title()}",
                    inline=False
                )
                
                if self.category.value:
                    embed.add_field(
                        name="🏷️ Category",
                        value=self.category.value,
                        inline=True
                    )
                
                if self.priority.value:
                    embed.add_field(
                        name="⚡ Priority",
                        value=self.priority.value,
                        inline=True
                    )
                
                if self.contact_permission.value:
                    embed.add_field(
                        name="📞 Contact Permission",
                        value=self.contact_permission.value,
                        inline=True
                    )
                
                embed.add_field(
                    name="🎯 What Happens Next?",
                    value="• Your feedback is reviewed by our team\n• We'll consider it for future improvements\n• You may be contacted if follow-up is needed",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Quick Feedback",
                    value="For quick feedback anytime, use `/feedback <your message>`",
                    inline=False
                )
                
            else:
                embed = error_embed(
                    "❌ Submission Failed",
                    "Failed to save your feedback. Please try again later."
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error submitting feedback: {str(e)}",
                ephemeral=True
            )

class BugReportModal(discord.ui.Modal, title="🐛 Report a Bug"):
    """Modal for bug reports."""
    
    def __init__(self):
        super().__init__()
    
    bug_title = discord.ui.TextInput(
        label="Bug Title",
        placeholder="Brief description of the bug (e.g., 'Profile not saving')",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    bug_description = discord.ui.TextInput(
        label="Bug Description",
        placeholder="Describe what happened, what you expected, and what actually happened...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    steps_to_reproduce = discord.ui.TextInput(
        label="Steps to Reproduce",
        placeholder="1. Go to...\n2. Click on...\n3. See error...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    expected_behavior = discord.ui.TextInput(
        label="Expected Behavior",
        placeholder="What should have happened instead?",
        required=True,
        max_length=300,
        style=discord.TextStyle.short
    )
    
    additional_info = discord.ui.TextInput(
        label="Additional Information (Optional)",
        placeholder="Browser, device, time of day, or any other relevant details...",
        required=False,
        max_length=300,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle bug report submission."""
        try:
            # Validate inputs
            if not self.bug_title.value.strip():
                await interaction.response.send_message(
                    "❌ Bug title is required!",
                    ephemeral=True
                )
                return
            
            if not self.bug_description.value.strip():
                await interaction.response.send_message(
                    "❌ Bug description is required!",
                    ephemeral=True
                )
                return
            
            if not self.steps_to_reproduce.value.strip():
                await interaction.response.send_message(
                    "❌ Steps to reproduce are required!",
                    ephemeral=True
                )
                return
            
            if not self.expected_behavior.value.strip():
                await interaction.response.send_message(
                    "❌ Expected behavior is required!",
                    ephemeral=True
                )
                return
            
            # Get the feedback cog to save the bug report
            cog = interaction.client.get_cog('FeedbackCog')
            if not cog:
                await interaction.response.send_message(
                    "❌ Feedback system not available.",
                    ephemeral=True
                )
                return
            
            # Create comprehensive bug report
            bug_report = f"**Bug Title:** {self.bug_title.value.strip()}\n\n"
            bug_report += f"**Description:** {self.bug_description.value.strip()}\n\n"
            bug_report += f"**Steps to Reproduce:**\n{self.steps_to_reproduce.value.strip()}\n\n"
            bug_report += f"**Expected Behavior:** {self.expected_behavior.value.strip()}\n\n"
            
            if self.additional_info.value:
                bug_report += f"**Additional Info:** {self.additional_info.value.strip()}"
            
            # Save bug report
            success = await cog.save_feedback(
                interaction.user,
                f"Bug Report: {self.bug_title.value.strip()}",
                "Bug Report",
                bug_report,
                True  # Detailed feedback
            )
            
            if success:
                embed = success_embed(
                    "🐛 Bug Report Submitted!",
                    "Thank you for reporting this bug! Our team will investigate."
                )
                
                embed.add_field(
                    name="📋 Bug Details",
                    value=f"**Title:** {self.bug_title.value.strip()}\n**Priority:** High (Bug reports are prioritized)",
                    inline=False
                )
                
                embed.add_field(
                    name="🔍 What Happens Next?",
                    value="• Your bug report is reviewed by our development team\n• We'll investigate and fix the issue\n• You'll be notified when it's resolved",
                    inline=False
                )
                
            else:
                embed = error_embed(
                    "❌ Submission Failed",
                    "Failed to submit your bug report. Please try again later."
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error submitting bug report: {str(e)}",
                ephemeral=True
            )

class FeatureRequestModal(discord.ui.Modal, title="💡 Request a Feature"):
    """Modal for feature requests."""
    
    def __init__(self):
        super().__init__()
    
    feature_title = discord.ui.TextInput(
        label="Feature Title",
        placeholder="Brief description of the feature (e.g., 'Dark mode theme')",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    feature_description = discord.ui.TextInput(
        label="Feature Description",
        placeholder="Describe the feature you'd like to see, why it's useful, and how it would work...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    use_case = discord.ui.TextInput(
        label="Use Case",
        placeholder="How would this feature help users? What problem does it solve?",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    priority = discord.ui.TextInput(
        label="Priority Level",
        placeholder="How important is this feature? (Low, Medium, High, Critical)",
        required=True,
        max_length=20,
        style=discord.TextStyle.short
    )
    
    additional_ideas = discord.ui.TextInput(
        label="Additional Ideas (Optional)",
        placeholder="Any related features, design ideas, or implementation suggestions...",
        required=False,
        max_length=300,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle feature request submission."""
        try:
            # Validate inputs
            if not self.feature_title.value.strip():
                await interaction_response.send_message(
                    "❌ Feature title is required!",
                    ephemeral=True
                )
                return
            
            if not self.feature_description.value.strip():
                await interaction.response.send_message(
                    "❌ Feature description is required!",
                    ephemeral=True
                )
                return
            
            if not self.use_case.value.strip():
                await interaction.response.send_message(
                    "❌ Use case is required!",
                    ephemeral=True
                )
                return
            
            if not self.priority.value.strip():
                await interaction.response.send_message(
                    "❌ Priority level is required!",
                    ephemeral=True
                )
                return
            
            # Get the feedback cog to save the feature request
            cog = interaction.client.get_cog('FeedbackCog')
            if not cog:
                await interaction.response.send_message(
                    "❌ Feedback system not available.",
                    ephemeral=True
                )
                return
            
            # Create comprehensive feature request
            feature_request = f"**Feature Title:** {self.feature_title.value.strip()}\n\n"
            feature_request += f"**Description:** {self.feature_description.value.strip()}\n\n"
            feature_request += f"**Use Case:** {self.use_case.value.strip()}\n\n"
            feature_request += f"**Priority:** {self.priority.value.strip()}\n\n"
            
            if self.additional_ideas.value:
                feature_request += f"**Additional Ideas:** {self.additional_ideas.value.strip()}"
            
            # Save feature request
            success = await cog.save_feedback(
                interaction.user,
                f"Feature Request: {self.feature_title.value.strip()}",
                "Feature Request",
                feature_request,
                True  # Detailed feedback
            )
            
            if success:
                embed = success_embed(
                    "💡 Feature Request Submitted!",
                    "Thank you for your feature request! We'll consider it for future updates."
                )
                
                embed.add_field(
                    name="📋 Feature Details",
                    value=f"**Title:** {self.feature_title.value.strip()}\n**Priority:** {self.priority.value.strip()}",
                    inline=False
                )
                
                embed.add_field(
                    name="🔮 What Happens Next?",
                    value="• Your feature request is reviewed by our team\n• We'll evaluate feasibility and impact\n• You'll be notified of our decision",
                    inline=False
                )
                
            else:
                embed = error_embed(
                    "❌ Submission Failed",
                    "Failed to submit your feature request. Please try again later."
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error submitting feature request: {str(e)}",
                ephemeral=True
            )

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