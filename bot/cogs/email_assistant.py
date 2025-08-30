import discord
from discord import app_commands
from discord.ext import commands
import logging
import re
from typing import Optional, Dict, List
from datetime import datetime
from bot.email.template_manager import template_manager
from bot.email.resend_client import ResendClient
from bot.email.email_logger import EmailLogger
from bot.email.models import TemplateCategory, TemplateTone
from config import Config

class DynamicEmailModal(discord.ui.Modal):
    """Dynamic modal that creates input fields based on template placeholders."""
    
    def __init__(self, template, category: str = None):
        super().__init__(title=f"📧 Compose Email: {template.name}")
        self.template = template
        self.category = category
        
        # Extract all placeholders from template
        self.placeholders = self._extract_placeholders(template)
        
        # Create dynamic input fields
        self.input_fields = {}
        self._create_input_fields()
        
        # Add all fields to modal
        for field in self.input_fields.values():
            self.add_item(field)
    
    def _extract_placeholders(self, template) -> List[str]:
        """Extract all placeholders from template subject and body."""
        placeholders = set()
        
        # Extract from subject
        subject_placeholders = re.findall(r'\{([^}]+)\}', template.subject)
        placeholders.update(subject_placeholders)
        
        # Extract from body
        body_placeholders = re.findall(r'\{([^}]+)\}', template.body)
        placeholders.update(body_placeholders)
        
        return sorted(list(placeholders))
    
    def _create_input_fields(self):
        """Create appropriate input fields for each placeholder."""
        for placeholder in self.placeholders:
            field = self._create_field_for_placeholder(placeholder)
            self.input_fields[placeholder] = field
    
    def _create_field_for_placeholder(self, placeholder: str) -> discord.ui.TextInput:
        """Create the most appropriate input field for a given placeholder."""
        # Common field configurations
        field_configs = {
            'name': {
                'label': 'Recipient Name',
                'placeholder': 'Enter recipient\'s full name',
                'required': True,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'recipient_name': {
                'label': 'Recipient Name',
                'placeholder': 'Enter recipient\'s full name',
                'required': True,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'email': {
                'label': 'Email Address',
                'placeholder': 'recipient@example.com',
                'required': True,
                'max_length': 254,
                'style': discord.TextStyle.short
            },
            'recipient_email': {
                'label': 'Recipient Email',
                'placeholder': 'recipient@example.com',
                'required': True,
                'max_length': 254,
                'style': discord.TextStyle.short
            },
            'contact_email': {
                'label': 'Contact Email',
                'placeholder': 'your@email.com',
                'required': True,
                'max_length': 254,
                'style': discord.TextStyle.short
            },
            'sender_email': {
                'label': 'Your Email',
                'placeholder': 'your@email.com',
                'required': True,
                'max_length': 254,
                'style': discord.TextStyle.short
            },
            'sender_name': {
                'label': 'Your Name',
                'placeholder': 'Enter your name',
                'required': True,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'event_name': {
                'label': 'Event Name',
                'placeholder': 'e.g., Maximally Hackathon 2024',
                'required': True,
                'max_length': 200,
                'style': discord.TextStyle.short
            },
            'hackathon_name': {
                'label': 'Hackathon Name',
                'placeholder': 'e.g., Maximally Hackathon 2024',
                'required': True,
                'max_length': 200,
                'style': discord.TextStyle.short
            },
            'date': {
                'label': 'Event Date',
                'placeholder': 'e.g., December 15-17, 2024',
                'required': True,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'time': {
                'label': 'Event Time',
                'placeholder': 'e.g., 9:00 AM - 6:00 PM',
                'required': True,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'location': {
                'label': 'Event Location',
                'placeholder': 'e.g., Online, San Francisco, Hybrid',
                'required': True,
                'max_length': 200,
                'style': discord.TextStyle.short
            },
            'duration': {
                'label': 'Event Duration',
                'placeholder': 'e.g., 48 hours, 3 days, 1 week',
                'required': True,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'prize_pool': {
                'label': 'Prize Pool',
                'placeholder': 'e.g., $50,000, $25,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'organization': {
                'label': 'Organization Name',
                'placeholder': 'e.g., Maximally Inc.',
                'required': True,
                'max_length': 200,
                'style': discord.TextStyle.short
            },
            'participants': {
                'label': 'Number of Participants',
                'placeholder': 'e.g., 500, 1000+',
                'required': False,
                'max_length': 50,
                'style': discord.TextStyle.short
            },
            'theme': {
                'label': 'Event Theme',
                'placeholder': 'e.g., AI & Sustainability, Web3 Innovation',
                'required': False,
                'max_length': 200,
                'style': discord.TextStyle.short
            },
            'judges': {
                'label': 'Number of Judges',
                'placeholder': 'e.g., 15, 20+',
                'required': False,
                'max_length': 50,
                'style': discord.TextStyle.short
            },
            'min_sponsorship': {
                'label': 'Minimum Sponsorship Amount',
                'placeholder': 'e.g., $5,000, $10,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'title_amount': {
                'label': 'Title Sponsor Amount',
                'placeholder': 'e.g., $25,000, $50,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'platinum_amount': {
                'label': 'Platinum Sponsor Amount',
                'placeholder': 'e.g., $15,000, $30,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'gold_amount': {
                'label': 'Gold Sponsor Amount',
                'placeholder': 'e.g., $10,000, $20,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'custom_amount': {
                'label': 'Custom Package Amount',
                'placeholder': 'e.g., $8,000, $12,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'original_amount': {
                'label': 'Original Package Amount',
                'placeholder': 'e.g., $10,000, $15,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'deadline': {
                'label': 'Deadline',
                'placeholder': 'e.g., December 1st, 2024',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'final_deadline': {
                'label': 'Final Deadline',
                'placeholder': 'e.g., December 10th, 2024',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'payment_deadline': {
                'label': 'Payment Deadline',
                'placeholder': 'e.g., December 5th, 2024',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'weeks_until': {
                'label': 'Weeks Until Event',
                'placeholder': 'e.g., 4, 6, 8',
                'required': False,
                'max_length': 50,
                'style': discord.TextStyle.short
            },
            'days_left': {
                'label': 'Days Left',
                'placeholder': 'e.g., 15, 30, 45',
                'required': False,
                'max_length': 50,
                'style': discord.TextStyle.short
            },
            'amount': {
                'label': 'Amount',
                'placeholder': 'e.g., $5,000, $10,000',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'package_type': {
                'label': 'Package Type',
                'placeholder': 'e.g., Gold, Platinum, Title',
                'required': False,
                'max_length': 100,
                'style': discord.TextStyle.short
            },
            'phone': {
                'label': 'Phone Number',
                'placeholder': 'e.g., +1 (555) 123-4567',
                'required': False,
                'max_length': 50,
                'style': discord.TextStyle.short
            }
        }
        
        # Get configuration for this placeholder
        config = field_configs.get(placeholder, {
            'label': placeholder.replace('_', ' ').title(),
            'placeholder': f'Enter {placeholder.replace("_", " ")}',
            'required': True,
            'max_length': 200,
            'style': discord.TextStyle.short
        })
        
        # Create the field
        field = discord.ui.TextInput(
            label=config['label'],
            placeholder=config['placeholder'],
            required=config['required'],
            max_length=config['max_length'],
            style=config['style']
        )
        
        return field

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Collect all placeholder values
            placeholder_values = {}
            for placeholder, field in self.input_fields.items():
                placeholder_values[placeholder] = field.value
            
            # Fill placeholders in the template
            filled_subject = self.template.subject
            filled_body = self.template.body
            
            for placeholder, value in placeholder_values.items():
                placeholder_text = f"{{{placeholder}}}"
                filled_subject = filled_subject.replace(placeholder_text, value)
                filled_body = filled_body.replace(placeholder_text, value)
            
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
            
            # Add key details
            if 'recipient_name' in placeholder_values:
                embed.add_field(
                    name="👤 Recipient",
                    value=placeholder_values['recipient_name'],
                    inline=True
                )
            
            if 'event_name' in placeholder_values:
                embed.add_field(
                    name="🎯 Event",
                    value=placeholder_values['event_name'],
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
                to=self.placeholder_values.get('recipient_email') or self.placeholder_values.get('email'),
                subject=self.processed_template.get('subject'),
                body=self.processed_template.get('body')
            )
            
            # Log the email
            await cog.email_logger.log_email(
                template_id=self.template.id,
                template_name=self.template.name,
                recipient_email=self.placeholder_values.get('recipient_email') or self.placeholder_values.get('email'),
                recipient_name=self.placeholder_values.get('recipient_name') or self.placeholder_values.get('name'),
                status="sent" if result['success'] else "failed",
                sent_by=interaction.user.id,
                error_message=result.get('error')
            )
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Email Sent Successfully!",
                    description=f"**To:** {self.placeholder_values.get('recipient_name', 'N/A')}\n**Template:** {self.template.category}/{self.template.name}",
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

            # Open the dynamic email composition modal
            modal = DynamicEmailModal(email_template, category)
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

            # Open the dynamic email composition modal
            modal = DynamicEmailModal(email_template, category)
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
                    # Count placeholders in this template
                    placeholders = re.findall(r'\{([^}]+)\}', template.subject + template.body)
                    unique_placeholders = len(set(placeholders))
                    template_list.append(f"• **{template.name}** - {unique_placeholders} placeholders")

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
