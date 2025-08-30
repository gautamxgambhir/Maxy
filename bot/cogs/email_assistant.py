import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from bot.email.template_manager import template_manager
from bot.email.resend_client import ResendClient
from bot.email.email_logger import EmailLogger
from bot.email.placeholder_processor import placeholder_processor
from bot.email.models import TemplateCategory, TemplateTone
from config import Config

class EmailActionView(discord.ui.View):

    def __init__(self, template, filled_subject: str, filled_body: str, placeholders: dict):
        super().__init__(timeout=600)
        self.template = template
        self.filled_subject = filled_subject
        self.filled_body = filled_body
        self.placeholders = placeholders

    @discord.ui.button(label="📋 Copy Draft", style=discord.ButtonStyle.primary)
    async def copy_draft(self, interaction: discord.Interaction, button: discord.ui.Button):
        content = f"Subject: {self.filled_subject}\n\n{self.filled_body}"
        embed = discord.Embed(
            title="📋 Email Draft Ready to Copy",
            description=f"**Template:** {self.template.category}/{self.template.name}\n**Tone:** {self.template.tone}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Content",
            value=f"```\n{content[:1800]}\n```",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📧 Quick Send", style=discord.ButtonStyle.success)
    async def quick_send(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = QuickSendModal(self.template, self.filled_subject, self.filled_body)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔄 Customize", style=discord.ButtonStyle.secondary)
    async def customize(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomizeEmailModal(self.template, self.placeholders, self.filled_subject, self.filled_body)
        await interaction.response.send_modal(modal)

class QuickSendModal(discord.ui.Modal, title="Quick Send Email"):
    """Modal for quick email sending."""

    def __init__(self, template, subject: str, body: str):
        super().__init__()
        self.template = template
        self.subject = subject
        self.body = body

    recipient_email = discord.ui.TextInput(
        label="Recipient Email",
        placeholder="recipient@example.com",
        required=True,
        max_length=254
    )

    recipient_name = discord.ui.TextInput(
        label="Recipient Name",
        placeholder="John Doe",
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle quick send submission."""
        try:
            cog = interaction.client.get_cog('EmailAssistantCog')
            if not cog:
                await interaction.response.send_message("❌ Email assistant not available.", ephemeral=True)
                return

            result = await cog.resend_client.send_email(
                to=self.recipient_email.value,
                subject=self.subject,
                body=self.body
            )

            await cog.email_logger.log_email(
                template_id=self.template.id,
                template_name=self.template.name,
                recipient_email=self.recipient_email.value,
                recipient_name=self.recipient_name.value,
                status="sent" if result['success'] else "failed",
                sent_by=interaction.user.id,
                error_message=result.get('error')
            )

            if result['success']:
                embed = discord.Embed(
                    title="✅ Email Sent Successfully!",
                    description=f"**To:** {self.recipient_name.value}\n**Template:** {self.template.category}/{self.template.name}",
                    color=discord.Color.green()
                )
                embed.set_footer(text="💡 Tip: Use /email-analytics to track your email performance")
            else:
                embed = discord.Embed(
                    title="❌ Email Failed",
                    description=f"**Error:** {result.get('error', 'Unknown error')}",
                    color=discord.Color.red()
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ Failed to send email.", ephemeral=True)

class CustomizeEmailModal(discord.ui.Modal, title="Customize Email"):
    """Modal for customizing email content."""

    def __init__(self, template, placeholders: dict, subject: str, body: str):
        super().__init__()
        self.template = template
        self.placeholders = placeholders
        self.original_subject = subject
        self.original_body = body

    custom_subject = discord.ui.TextInput(
        label="Custom Subject (leave empty to keep original)",
        placeholder="Custom subject line...",
        required=False,
        max_length=200
    )

    additional_content = discord.ui.TextInput(
        label="Additional Content (added to end)",
        placeholder="Add any additional content here...",
        required=False,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle customization submission."""
        try:
            final_subject = self.custom_subject.value.strip() if self.custom_subject.value.strip() else self.original_subject
            final_body = self.original_body
            if self.additional_content.value.strip():
                final_body += f"\n\n{self.additional_content.value.strip()}"

            view = EmailActionView(self.template, final_subject, final_body, self.placeholders)

            embed = discord.Embed(
                title="✨ Customized Email Ready",
                description="Your customized email is ready! Choose an action below:",
                color=discord.Color.purple()
            )

            embed.add_field(
                name="📧 Subject",
                value=final_subject,
                inline=False
            )

            body_preview = final_body[:300] + ("..." if len(final_body) > 300 else "")
            embed.add_field(
                name="📝 Content Preview",
                value=body_preview,
                inline=False
            )

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ Failed to customize email.", ephemeral=True)

class EmailAssistantCog(commands.Cog):
    """Comprehensive email assistant with advanced features."""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.template_manager = template_manager
        self.resend_client = ResendClient(
            api_key=Config.RESEND_API_KEY,
            default_from=Config.EMAIL_FROM_ADDRESS
        ) if Config.RESEND_API_KEY else None
        self.email_logger = EmailLogger()
        self.placeholder_processor = placeholder_processor

        self.user_context = {}
        self.template_cache = {}

    async def cog_load(self):
        """Initialize when loaded."""
        if not self.resend_client:
            self.logger.warning("Email sending disabled - configure RESEND_API_KEY")
        else:
            self.logger.info("Email sending enabled - Resend API connected")

        # Seed templates if needed
        await self.template_manager.seed_templates_async()

        await self._preload_popular_templates()
        self.logger.info("Email Assistant loaded with advanced features")

    async def cog_unload(self):
        """Cleanup when unloaded."""
        self.logger.info("Email Assistant unloaded")

    async def _preload_popular_templates(self):
        """Pre-load frequently used templates for faster access."""
        try:
            popular_categories = ['judges', 'sponsors', 'participants']
            for category in popular_categories:
                templates = await self.template_manager.get_available_templates(category)
                self.template_cache[category] = templates[:5]
        except Exception as e:
            self.logger.warning(f"Failed to preload templates: {e}")

    @app_commands.command(
        name="email",
        description="Email assistant for hackathon operations"
    )
    @app_commands.describe(
        action="What would you like to do?",
        category="Email template category (optional)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="📋 Browse Templates", value="browse"),
        app_commands.Choice(name="📧 Send Email", value="send"),
        app_commands.Choice(name="📊 View Statistics", value="stats"),
        app_commands.Choice(name="📜 View History", value="history"),
        app_commands.Choice(name="🔧 Manage Templates", value="manage"),
        app_commands.Choice(name="❓ Help", value="help")
    ])
    async def email_command(self, interaction: discord.Interaction,
                           action: str, category: Optional[str] = None):
        """Main email command with multiple actions."""
        try:
            # Defer the response since we might do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            if action == "browse":
                await self._handle_browse_templates(interaction, category)
            elif action == "send":
                await self._handle_send_email_workflow(interaction)
            elif action == "stats":
                await self._handle_view_stats(interaction)
            elif action == "history":
                await self._handle_view_history(interaction)
            elif action == "manage":
                await self._handle_manage_templates(interaction)
            elif action == "help":
                await self._handle_help(interaction)
            else:
                try:
                    await interaction.followup.send(
                        "❌ Invalid action selected.",
                        ephemeral=True
                    )
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send invalid action response - interaction already handled")

        except Exception as e:
            self.logger.error(f"Email command error: {e}")
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(
                        "❌ An error occurred. Please try again later.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                self.logger.error(f"Failed to send error followup: {followup_error}")

    async def _handle_browse_templates(self, interaction: discord.Interaction,
                                     category: Optional[str] = None):
        """Handle template browsing."""
        try:
            if category:
                templates = await self.template_manager.get_available_templates(category)
                if not templates:
                    try:
                        await interaction.followup.send(
                            f"📭 No templates found in category: **{category}**",
                            ephemeral=True
                        )
                    except (discord.errors.InteractionResponded, discord.errors.NotFound):
                        self.logger.warning("Could not send no templates response - interaction already handled")
                    return

                embed = discord.Embed(
                    title=f"📋 {category.title()} Templates",
                    color=discord.Color.blue()
                )

                template_list = []
                for template in templates[:10]:
                    template_list.append(f"• **{template.name}** ({template.tone}) - {len(template.placeholders)} placeholders")

                embed.description = "\n".join(template_list)

                if len(templates) > 10:
                    embed.set_footer(text=f"Showing 10 of {len(templates)} templates")

                try:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send browse templates response - interaction already handled")

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

                try:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send categories response - interaction already handled")

        except Exception as e:
            self.logger.error(f"Browse templates error: {e}")
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(
                        "❌ Failed to browse templates.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                self.logger.error(f"Failed to send browse error followup: {followup_error}")

    async def _handle_send_email_workflow(self, interaction: discord.Interaction):
        """Handle the email sending workflow."""
        try:
            if not self.resend_client:
                try:
                    await interaction.followup.send(
                        "❌ Email sending is not configured. Please set up RESEND_API_KEY in your environment.",
                        ephemeral=True
                    )
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send email config error - interaction already handled")
                return

            categories = [cat.value for cat in TemplateCategory]
            embed = discord.Embed(
                title="📧 Send Email - Select Category",
                description="Choose the type of email you want to send:",
                color=discord.Color.green()
            )

            for i, category in enumerate(categories, 1):
                embed.add_field(
                    name=f"{i}. {category.replace('-', ' ').title()}",
                    value=f"Use `/email-send category:{category}`",
                    inline=False
                )

            embed.set_footer(text="Use the command with the category parameter to continue")

            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.NotFound):
                self.logger.warning("Could not send send email workflow response - interaction already handled")

        except Exception as e:
            self.logger.error(f"Send email workflow error: {e}")
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(
                        "❌ Failed to start email workflow.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                self.logger.error(f"Failed to send workflow error followup: {followup_error}")

    async def _handle_view_stats(self, interaction: discord.Interaction):
        """Handle viewing email statistics."""
        try:
            stats = await self.email_logger.get_stats()

            embed = discord.Embed(
                title="📊 Email Statistics",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📧 Total Emails",
                value=str(stats['total_emails']),
                inline=True
            )

            embed.add_field(
                name="✅ Successful",
                value=str(stats['successful_emails']),
                inline=True
            )

            embed.add_field(
                name="📈 Success Rate",
                value=f"{stats['success_rate']:.1f}%",
                inline=True
            )

            embed.add_field(
                name="🕐 Recent Activity",
                value=f"{stats['recent_activity']} emails (7 days)",
                inline=False
            )

            if stats['popular_templates']:
                popular_list = []
                for i, template in enumerate(stats['popular_templates'][:5], 1):
                    popular_list.append(f"{i}. {template['template_name']} ({template['usage_count']})")

                embed.add_field(
                    name="🔥 Popular Templates",
                    value="\n".join(popular_list),
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"View stats error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to load statistics.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    async def _handle_view_history(self, interaction: discord.Interaction):
        """Handle viewing email history."""
        try:
            logs = await self.email_logger.get_logs({'limit': 10, 'sent_by': interaction.user.id})

            if not logs:
                await interaction.followup.send(
                    "📭 No email history found.",
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title="📜 Recent Email History",
                color=discord.Color.blue()
            )

            for log in logs[:10]:
                status_emoji = "✅" if log.status == "sent" else "❌"
                embed.add_field(
                    name=f"{status_emoji} {log.template_name}",
                    value=f"**To:** {log.recipient_name}\n**Date:** {log.sent_at.strftime('%Y-%m-%d %H:%M')}",
                    inline=False
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"View history error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to load email history.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    async def _handle_manage_templates(self, interaction: discord.Interaction):
        """Handle template management interface."""
        try:
            embed = discord.Embed(
                title="🔧 Template Management",
                description="Available management commands:",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="📋 List Templates",
                value="`/email category:<category>`",
                inline=False
            )

            embed.add_field(
                name="➕ Create Template",
                value="`/email-create-template`",
                inline=False
            )

            embed.add_field(
                name="✏️ Edit Template",
                value="`/email-edit-template`",
                inline=False
            )

            embed.add_field(
                name="🗑️ Delete Template",
                value="`/email-delete-template`",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Manage templates error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to show template management options.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    async def _handle_help(self, interaction: discord.Interaction):
        """Handle help command."""
        try:
            embed = discord.Embed(
                title="❓ Email Assistant Help",
                description="Complete guide to using the email assistant:",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📧 Main Commands",
                value="• `/email` - Browse templates and get help\n• `/email-send` - Send email directly\n• `/email-copy` - Copy draft text\n• `/email-list` - List all templates",
                inline=False
            )

            embed.add_field(
                name="🔧 Template Management",
                value="• `/email-create-template` - Create new template\n• `/email-edit-template` - Edit existing template\n• `/email-delete-template` - Delete template\n• `/email-preview` - Preview with placeholders",
                inline=False
            )

            embed.add_field(
                name="📊 Analytics",
                value="• `/email action:stats` - View email statistics\n• `/email action:history` - View sent email history",
                inline=False
            )

            embed.add_field(
                name="🔧 Placeholders",
                value="Use format: `key:value,key:value`\nExample: `name:John,event_name:Hackathon`",
                inline=False
            )

            embed.set_footer(text="💡 Tip: Use /email action:help anytime for this guide")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Help error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to show help.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @app_commands.command(
        name="email-send",
        description="Send email using template"
    )
    @app_commands.describe(
        category="Template category",
        template="Template name",
        recipient_email="Recipient email address",
        recipient_name="Recipient name",
        placeholders="Placeholder values (optional, format: key:value,key:value)"
    )
    async def email_send_command(self, interaction: discord.Interaction,
                                category: str, template: str,
                                recipient_email: str, recipient_name: str,
                                placeholders: Optional[str] = None):
        """Send email using template."""
        try:
            # Defer the response since we do database operations and email sending
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            if not self.resend_client:
                try:
                    await interaction.followup.send(
                        "❌ Email sending is not configured.",
                        ephemeral=True
                    )
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send email config error - interaction already handled")
                return

            email_template = await self.template_manager.get_template(category, template)
            if not email_template:
                try:
                    await interaction.followup.send(
                        f"❌ Template not found: **{category}/{template}**",
                        ephemeral=True
                    )
                except (discord.errors.InteractionResponded, discord.errors.NotFound):
                    self.logger.warning("Could not send template not found error - interaction already handled")
                return

            placeholder_values = {}
            if placeholders:
                for pair in placeholders.split(','):
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        placeholder_values[key.strip()] = value.strip()

            filled_subject = self.placeholder_processor.fill_placeholders(
                email_template.subject, placeholder_values
            )
            filled_body = self.placeholder_processor.fill_placeholders(
                email_template.body, placeholder_values
            )

            result = await self.resend_client.send_email(
                to=recipient_email,
                subject=filled_subject,
                body=filled_body
            )

            await self.email_logger.log_email(
                template_id=email_template.id,
                template_name=email_template.name,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                status="sent" if result['success'] else "failed",
                sent_by=interaction.user.id,
                error_message=result.get('error')
            )

            if result['success']:
                embed = discord.Embed(
                    title="✅ Email Sent Successfully!",
                    description=f"**To:** {recipient_name} <{recipient_email}>\n**Template:** {category}/{template}",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Email Failed",
                    description=f"**Error:** {result.get('error', 'Unknown error')}",
                    color=discord.Color.red()
                )

            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.NotFound):
                self.logger.warning("Could not send email result - interaction already handled")

        except Exception as e:
            self.logger.error(f"Email send error: {e}")
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(
                        "❌ Failed to send email.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                self.logger.error(f"Failed to send email error followup: {followup_error}")

    @app_commands.command(
        name="email-copy",
        description="Copy email draft text"
    )
    @app_commands.describe(
        category="Template category",
        template="Template name",
        placeholders="Placeholder values (optional, format: key:value,key:value)"
    )
    async def email_copy_command(self, interaction: discord.Interaction,
                                category: str, template: str,
                                placeholders: Optional[str] = None):
        """Copy email draft text."""
        try:
            # Defer the response since we do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            email_template = await self.template_manager.get_template(category, template)
            if not email_template:
                await interaction.followup.send(
                    f"❌ Template not found: **{category}/{template}**",
                    ephemeral=True
                )
                return

            placeholder_values = {}
            if placeholders:
                for pair in placeholders.split(','):
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        placeholder_values[key.strip()] = value.strip()

            filled_subject = self.placeholder_processor.fill_placeholders(
                email_template.subject, placeholder_values
            )
            filled_body = self.placeholder_processor.fill_placeholders(
                email_template.body, placeholder_values
            )

            content = f"Subject: {filled_subject}\n\n{filled_body}"

            embed = discord.Embed(
                title="📋 Email Draft Ready to Copy",
                description=f"**Template:** {category}/{template}",
                color=discord.Color.blue()
            )

            if len(content) > 1800:
                content = content[:1800] + "..."

            embed.add_field(
                name="Content",
                value=f"```\n{content}\n```",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Email copy error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to generate email draft.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

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
            # Defer the response since we do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            if category:
                templates = await self.template_manager.get_available_templates(category)
                if not templates:
                    try:
                        await interaction.followup.send(
                            f"📭 No templates found in category: **{category}**",
                            ephemeral=True
                        )
                    except (discord.errors.InteractionResponded, discord.errors.NotFound):
                        self.logger.warning("Could not send no templates response - interaction already handled")
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

            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.NotFound):
                self.logger.warning("Could not send list templates response - interaction already handled")

        except Exception as e:
            self.logger.error(f"Email list error: {e}")
            try:
                if not interaction.is_expired():
                    await interaction.followup.send(
                        "❌ Failed to list templates.",
                        ephemeral=True
                    )
            except Exception as followup_error:
                self.logger.error(f"Failed to send list error followup: {followup_error}")

    @app_commands.command(
        name="email-preview",
        description="Preview an email template with placeholder values"
    )
    @app_commands.describe(
        category="Email template category",
        template="Template name",
        placeholders="Placeholder values as key:value pairs"
    )
    async def email_preview_command(self, interaction: discord.Interaction,
                                   category: str, template: str,
                                   placeholders: str = ""):
        """Preview email template with filled placeholders."""
        try:
            # Defer the response since we do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            email_template = await self.template_manager.get_template(category, template)
            if not email_template:
                await interaction.followup.send(
                    f"❌ Template not found: **{category}/{template}**",
                    ephemeral=True
                )
                return

            placeholder_values = {}
            if placeholders:
                for pair in placeholders.split(','):
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        placeholder_values[key.strip()] = value.strip()

            preview = self.placeholder_processor.preview_filled_template(
                f"**Subject:** {email_template.subject}\n\n**Body:**\n{email_template.body}",
                placeholder_values
            )

            embed = discord.Embed(
                title=f"👀 Preview - {email_template.name}",
                description=f"**Category:** {category} | **Tone:** {email_template.tone}",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📊 Completion Status",
                value=f"**Filled:** {preview['filled_placeholders']}/{preview['total_placeholders']} "
                      f"({preview['completion_percentage']:.0f}%)",
                inline=False
            )

            if preview['missing_placeholders']:
                missing_list = [f"• {p}" for p in preview['missing_placeholders']]
                embed.add_field(
                    name="⚠️ Missing Placeholders",
                    value="\n".join(missing_list),
                    inline=False
                )

            preview_text = preview['preview']
            if len(preview_text) > 1000:
                preview_text = preview_text[:1000] + "..."

            embed.add_field(
                name="📧 Preview",
                value=preview_text,
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Email preview error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to generate preview.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @app_commands.command(
        name="email-create-template",
        description="Create a new email template"
    )
    @app_commands.describe(
        category="Template category",
        name="Template name",
        subject="Email subject line",
        body="Email body content",
        tone="Template tone"
    )
    @app_commands.choices(
        category=[app_commands.Choice(name=cat.value.replace('-', ' ').title(), value=cat.value)
                 for cat in TemplateCategory],
        tone=[app_commands.Choice(name=tone.value.title(), value=tone.value)
              for tone in TemplateTone]
    )
    async def email_create_template_command(self, interaction: discord.Interaction,
                                           category: str, name: str, subject: str,
                                           body: str, tone: str = "formal"):
        """Create a new email template."""
        try:
            # Defer the response since we do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            template = await self.template_manager.add_template(
                category=category,
                name=name,
                subject=subject,
                body=body,
                tone=tone
            )

            if template:
                embed = discord.Embed(
                    title="✅ Template Created",
                    description=f"**{category}/{name}** has been created successfully!",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="📋 Details",
                    value=f"**Category:** {category}\n**Tone:** {tone}\n**Placeholders:** {len(template.placeholders)}",
                    inline=False
                )

                if template.placeholders:
                    placeholder_list = [f"• {p}" for p in template.placeholders]
                    embed.add_field(
                        name="🔧 Placeholders Found",
                        value="\n".join(placeholder_list),
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="❌ Template Creation Failed",
                    description="Template with this name may already exist in the category.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Create template error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to create template.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @app_commands.command(
        name="email-edit-template",
        description="Edit an existing email template"
    )
    @app_commands.describe(
        category="Template category",
        name="Template name",
        new_subject="New subject line (leave empty to keep current)",
        new_body="New body content (leave empty to keep current)",
        new_tone="New tone (leave empty to keep current)"
    )
    @app_commands.choices(
        category=[app_commands.Choice(name=cat.value.replace('-', ' ').title(), value=cat.value)
                 for cat in TemplateCategory],
        new_tone=[app_commands.Choice(name=tone.value.title(), value=tone.value)
                 for tone in TemplateTone]
    )
    async def email_edit_template_command(self, interaction: discord.Interaction,
                                         category: str, name: str,
                                         new_subject: Optional[str] = None,
                                         new_body: Optional[str] = None,
                                         new_tone: Optional[str] = None):
        """Edit an existing email template."""
        try:
            # Defer the response since we do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            existing_template = await self.template_manager.get_template(category, name)
            if not existing_template:
                await interaction.followup.send(
                    f"❌ Template not found: **{category}/{name}**",
                    ephemeral=True
                )
                return

            updates = {}
            if new_subject:
                updates['subject'] = new_subject
            if new_body:
                updates['body'] = new_body
            if new_tone:
                updates['tone'] = new_tone

            if not updates:
                await interaction.followup.send(
                    "⚠️ No changes specified. Use the parameters to update subject, body, or tone.",
                    ephemeral=True
                )
                return

            success = await self.template_manager.update_template(existing_template.id, updates)

            if success:
                embed = discord.Embed(
                    title="✅ Template Updated",
                    description=f"**{category}/{name}** has been updated successfully!",
                    color=discord.Color.green()
                )

                changes_list = []
                if new_subject:
                    changes_list.append(f"• Subject: `{existing_template.subject}` → `{new_subject}`")
                if new_body:
                    changes_list.append("• Body content updated")
                if new_tone:
                    changes_list.append(f"• Tone: `{existing_template.tone}` → `{new_tone}`")

                embed.add_field(
                    name="📝 Changes Made",
                    value="\n".join(changes_list),
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Template Update Failed",
                    description="Failed to update the template. Please try again.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Edit template error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to update template.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

    @app_commands.command(
        name="email-delete-template",
        description="Delete an email template"
    )
    @app_commands.describe(
        category="Template category",
        name="Template name",
        confirm="Type 'DELETE' to confirm deletion"
    )
    @app_commands.choices(
        category=[app_commands.Choice(name=cat.value.replace('-', ' ').title(), value=cat.value)
                 for cat in TemplateCategory]
    )
    async def email_delete_template_command(self, interaction: discord.Interaction,
                                           category: str, name: str, confirm: str = ""):
        """Delete an email template."""
        try:
            # Defer the response since we do database operations
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
            except (discord.errors.InteractionResponded, discord.errors.HTTPException):
                pass

            if confirm != "DELETE":
                embed = discord.Embed(
                    title="⚠️ Confirmation Required",
                    description=f"To delete template **{category}/{name}**, type `DELETE` in the confirm parameter.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            template = await self.template_manager.get_template(category, name)
            if not template:
                await interaction.followup.send(
                    f"❌ Template not found: **{category}/{name}**",
                    ephemeral=True
                )
                return

            success = await self.template_manager.delete_template(template.id)

            if success:
                embed = discord.Embed(
                    title="🗑️ Template Deleted",
                    description=f"**{category}/{name}** has been permanently deleted.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Deletion Failed",
                    description="Failed to delete the template. Please try again.",
                    color=discord.Color.red()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Delete template error: {e}")
            try:
                await interaction.followup.send(
                    "❌ Failed to delete template.",
                    ephemeral=True
                )
            except Exception as followup_error:
                self.logger.error(f"Failed to send followup: {followup_error}")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(EmailAssistantCog(bot))