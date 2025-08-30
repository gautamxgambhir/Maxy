import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
from datetime import datetime
from bot.email.template_manager import template_manager
from bot.email.resend_client import ResendClient
from bot.email.email_logger import EmailLogger
from bot.email.models import TemplateCategory, TemplateTone
from config import Config

class EmailCompositionModal(discord.ui.Modal, title="📧 Compose Email"):
    """Modal for email composition with placeholders."""
    
    def __init__(self, template, category: str = None):
        super().__init__()
        self.template = template
        self.category = category
        
        # Create required fields
        self.recipient_name = discord.ui.TextInput(
            label="Recipient Name",
            placeholder="Enter recipient's full name",
            required=True,
            max_length=100,
            style=discord.TextStyle.short
        )
        
        self.recipient_email = discord.ui.TextInput(
            label="Recipient Email",
            placeholder="recipient@example.com",
            required=True,
            max_length=254,
            style=discord.TextStyle.short
        )
        
        self.sender_name = discord.ui.TextInput(
            label="Your Name",
            placeholder="Enter your name",
            required=True,
            max_length=100,
            style=discord.TextStyle.short
        )
        
        self.sender_email = discord.ui.TextInput(
            label="Your Email",
            placeholder="your@email.com",
            required=True,
            max_length=254,
            style=discord.TextStyle.short
        )
        
        # Add fields to modal
        self.add_item(self.recipient_name)
        self.add_item(self.recipient_email)
        self.add_item(self.sender_name)
        self.add_item(self.sender_email)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Fill placeholders in the template
            filled_subject = self.template.subject
            filled_body = self.template.body
            
            # Simple placeholder replacement
            placeholder_values = {
                'recipient_name': self.recipient_name.value,
                'recipient_email': self.recipient_email.value,
                'sender_name': self.sender_name.value,
                'sender_email': self.sender_email.value,
                'hackathon_name': 'Maximally Hackathon',
                'event_date': 'TBD',
                'event_location': 'Online'
            }
            
            for key, value in placeholder_values.items():
                placeholder = f"{{{key}}}"
                filled_subject = filled_subject.replace(placeholder, value)
                filled_body = filled_body.replace(placeholder, value)
            
            # Create confirmation view
            view = EmailConfirmationView(
                {
                    'subject': filled_subject,
                    'body': filled_body
                }, 
                placeholder_values, 
                self.template,
                self.category
            )
            
            embed = discord.Embed(
                title="📧 Email Ready to Send!",
                description="Review your email below and choose an action:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📨 Subject",
                value=filled_subject,
                inline=False
            )
            
            body_preview = filled_body
            if len(body_preview) > 1024:
                body_preview = body_preview[:1021] + "..."
            
            embed.add_field(
                name="📝 Body",
                value=body_preview,
                inline=False
            )
            
            embed.add_field(
                name="👤 Recipient",
                value=f"{placeholder_values.get('recipient_name', 'N/A')} ({placeholder_values.get('recipient_email', 'N/A')})",
                inline=True
            )
            
            embed.add_field(
                name="📋 Template",
                value=f"{self.template.category}/{self.template.name}",
                inline=True
            )
            
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error processing email: {str(e)}",
                ephemeral=True
            )

class EmailConfirmationView(discord.ui.View):
    """View for confirming and sending emails."""
    
    def __init__(self, processed_template, placeholder_values, template, category):
        super().__init__(timeout=300)
        self.processed_template = processed_template
        self.placeholder_values = placeholder_values
        self.template = template
        self.category = category

    @discord.ui.button(label="📧 Send Email", style=discord.ButtonStyle.success, emoji="✅")
    async def send_email(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the email."""
        try:
            # Get the email assistant cog
            cog = interaction.client.get_cog('EmailAssistantCog')
            if not cog:
                await interaction.response.send_message("❌ Email assistant not available.", ephemeral=True)
                return
            
            # Send email
            result = await cog.resend_client.send_email(
                to=self.placeholder_values.get('recipient_email'),
                subject=self.processed_template.get('subject'),
                body=self.processed_template.get('body')
            )
            
            # Log the email
            await cog.email_logger.log_email(
                template_id=self.template.id,
                template_name=self.template.name,
                recipient_email=self.placeholder_values.get('recipient_email'),
                recipient_name=self.placeholder_values.get('recipient_name'),
                status="sent" if result['success'] else "failed",
                sent_by=interaction.user.id,
                error_message=result.get('error')
            )
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Email Sent Successfully!",
                    description=f"**To:** {self.placeholder_values.get('recipient_name')}\n**Template:** {self.template.category}/{self.template.name}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="📧 Details",
                    value=f"**Subject:** {self.processed_template.get('subject')}\n**Sent at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Email Failed to Send",
                    description=f"**Error:** {result.get('error', 'Unknown error')}",
                    color=discord.Color.red()
                )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error sending email: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="📋 Copy Draft", style=discord.ButtonStyle.primary, emoji="📄")
    async def copy_draft(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Copy the email draft."""
        content = f"Subject: {self.processed_template.get('subject')}\n\n{self.processed_template.get('body')}"
        
        embed = discord.Embed(
            title="📋 Email Draft Copied",
            description="Copy the content below:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📧 Email Content",
            value=f"```\n{content[:1800]}\n```",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, emoji="🚫")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the email."""
        embed = discord.Embed(
            title="❌ Email Cancelled",
            description="Email composition has been cancelled.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)

class EmailAssistantCog(commands.Cog):
    """Email assistant for hackathon operations."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.template_manager = template_manager
        self.resend_client = ResendClient(
            api_key=Config.RESEND_API_KEY,
            default_from=Config.EMAIL_FROM_ADDRESS
        ) if Config.RESEND_API_KEY else None
        self.email_logger = EmailLogger()

    async def cog_load(self):
        """Initialize when loaded."""
        if not self.resend_client:
            self.logger.warning("Email sending disabled - configure RESEND_API_KEY")
        else:
            self.logger.info("Email sending enabled - Resend API connected")

        # Seed templates if needed
        await self.template_manager.seed_templates_async()
        self.logger.info("Email Assistant loaded")

    @app_commands.command(
        name="email-preview",
        description="Preview an email template with placeholder values"
    )
    @app_commands.describe(
        category="Email template category",
        template="Template name"
    )
    async def email_preview_command(self, interaction: discord.Interaction,
                                   category: str, template: str):
        """Preview email template with filled placeholders using modal."""
        try:
            # Get the template
            email_template = await self.template_manager.get_template(category, template)
            if not email_template:
                await interaction.response.send_message(
                    f"❌ Template not found: **{category}/{template}**",
                    ephemeral=True
                )
                return

            # Open the email composition modal
            modal = EmailCompositionModal(email_template, category)
            await interaction.response.send_modal(modal)

        except Exception as e:
            self.logger.error(f"Email preview error: {e}")
            await interaction.response.send_message(
                "❌ Failed to open email composition modal.",
                ephemeral=True
            )

    @app_commands.command(
        name="email-send",
        description="Send email using template"
    )
    @app_commands.describe(
        category="Template category",
        template="Template name"
    )
    async def email_send_command(self, interaction: discord.Interaction,
                                category: str, template: str):
        """Send email using template via modal."""
        try:
            if not self.resend_client:
                await interaction.response.send_message(
                    "❌ Email sending is not configured.",
                    ephemeral=True
                )
                return

            email_template = await self.template_manager.get_template(category, template)
            if not email_template:
                await interaction.response.send_message(
                    f"❌ Template not found: **{category}/{template}**",
                    ephemeral=True
                )
                return

            # Open the email composition modal
            modal = EmailCompositionModal(email_template, category)
            await interaction.response.send_modal(modal)

        except Exception as e:
            self.logger.error(f"Email send error: {e}")
            await interaction.response.send_message(
                "❌ Failed to open email composition modal.",
                ephemeral=True
            )

    @app_commands.command(
        name="email-list",
        description="List available email templates"
    )
    @app_commands.describe(
        category="Filter by category (optional)"
    )
    async def email_list_command(self, interaction: discord.Interaction,
                                category: Optional[str] = None):
        """List available email templates."""
        try:
            if category:
                templates = await self.template_manager.get_available_templates(category)
                if not templates:
                    await interaction.response.send_message(
                        f"📭 No templates found in category: **{category}**",
                        ephemeral=True
                    )
                    return

                embed = discord.Embed(
                    title=f"📋 {category.title()} Templates",
                    color=discord.Color.blue()
                )

                template_list = []
                for template in templates[:10]:
                    template_list.append(f"• **{template.name}** - {len(template.placeholders)} placeholders")

                embed.description = "\n".join(template_list)

                if len(templates) > 10:
                    embed.set_footer(text=f"Showing 10 of {len(templates)} templates")

            else:
                categories = [cat.value for cat in TemplateCategory]
                embed = discord.Embed(
                    title="📋 Email Template Categories",
                    description="Select a category to browse templates:",
                    color=discord.Color.blue()
                )

                for category in categories:
                    templates = await self.template_manager.get_available_templates(category)
                    embed.add_field(
                        name=f"📁 {category.replace('-', ' ').title()}",
                        value=f"{len(templates)} templates available",
                        inline=True
                    )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Email list error: {e}")
            await interaction.response.send_message(
                "❌ Failed to list templates.",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(EmailAssistantCog(bot))
