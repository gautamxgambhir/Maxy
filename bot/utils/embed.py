import discord
from config import Config
from typing import Optional, List, Dict, Any

# Enhanced color scheme for better visual hierarchy
class BotColors:
    PRIMARY = discord.Color.from_rgb(88, 101, 242)  # Discord Blurple
    SUCCESS = discord.Color.from_rgb(87, 242, 135)  # Green
    ERROR = discord.Color.from_rgb(237, 66, 69)     # Red
    WARNING = discord.Color.from_rgb(255, 202, 40)  # Yellow
    INFO = discord.Color.from_rgb(114, 137, 218)    # Light Blue
    SECONDARY = discord.Color.from_rgb(153, 170, 181) # Gray

def create_embed(title: str, description: str = None, color: discord.Color = BotColors.PRIMARY, 
                 thumbnail: bool = True, footer_text: str = None) -> discord.Embed:
    """Create a standardized embed with consistent styling."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    
    if thumbnail and Config.MAXIMALLY_LOGO_URL:
        embed.set_thumbnail(url=Config.MAXIMALLY_LOGO_URL)
    
    footer = footer_text or "Maximally : The global hackathon league"
    embed.set_footer(text=footer, icon_url=Config.MAXIMALLY_LOGO_URL if Config.MAXIMALLY_LOGO_URL else None)
    
    return embed

def success_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
    """Create a success embed with green color."""
    return create_embed(f"✅ {title}", description, BotColors.SUCCESS, **kwargs)

def error_embed(title: str, description: str = None, help_text: str = None, **kwargs) -> discord.Embed:
    """Create an error embed with red color and optional help text."""
    embed = create_embed(f"❌ {title}", description, BotColors.ERROR, **kwargs)
    if help_text:
        embed.add_field(name="💡 Need Help?", value=help_text, inline=False)
    return embed

def warning_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
    """Create a warning embed with yellow color."""
    return create_embed(f"⚠️ {title}", description, BotColors.WARNING, **kwargs)

def info_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
    """Create an info embed with blue color."""
    return create_embed(f"ℹ️ {title}", description, BotColors.INFO, **kwargs)

def profile_embed(profile: Dict[str, Any]) -> discord.Embed:
    """Create an enhanced profile embed with better formatting."""
    embed = create_embed(
        f"👤 Profile: {profile['name']}",
        f"**Discord:** {profile['discord_username']}",
        BotColors.PRIMARY
    )
    
    if profile.get('skills'):
        skills_formatted = profile['skills'].replace(',', ' • ')
        embed.add_field(
            name="🛠️ Skills", 
            value=f"```{skills_formatted}```", 
            inline=False
        )
    
    if profile.get('interests'):
        interests_formatted = profile['interests'].replace(',', ' • ')
        embed.add_field(
            name="❤️ Interests", 
            value=f"```{interests_formatted}```", 
            inline=False
        )
    
    if not profile.get('skills') and not profile.get('interests'):
        embed.add_field(
            name="📝 Profile Status",
            value="*Profile is incomplete. Add skills and interests to help others find you!*",
            inline=False
        )
    
    return embed

def search_results_embed(results: List[Dict[str, Any]]) -> discord.Embed:
    """Create an enhanced search results embed."""
    embed = create_embed(
        "🔍 Search Results",
        f"Found **{len(results)}** matching profiles:",
        BotColors.INFO
    )
    
    if not results:
        embed.description = "No profiles found matching your criteria."
        embed.add_field(
            name="💡 Tips for Better Results",
            value="• Try broader search terms\n• Check your spelling\n• Use common skill names",
            inline=False
        )
        return embed
    
    for i, profile in enumerate(results[:10], 1):
        skills = profile.get('skills', 'No skills listed')
        interests = profile.get('interests', 'No interests listed')
        
        # Truncate long text for better display
        skills = (skills[:50] + '...') if len(skills) > 50 else skills
        interests = (interests[:50] + '...') if len(interests) > 50 else interests
        
        embed.add_field(
            name=f"{i}. {profile['name']} (@{profile['discord_username']})",
            value=f"**🛠️ Skills:** {skills}\n**❤️ Interests:** {interests}",
            inline=False
        )
    
    if len(results) > 10:
        embed.set_footer(text=f"Showing 10 of {len(results)} results • Maximally : The global hackathon league")
    
    return embed

def base_embed(title: str, description: str = None, color: discord.Color = BotColors.PRIMARY) -> discord.Embed:
    """Create a basic embed with consistent styling."""
    return create_embed(title, description, color)

def volunteer_task_embed(task: Dict[str, Any]) -> discord.Embed:
    """Create an enhanced embed for a volunteer task."""
    status_emoji = "🟢" if task["status"] == "open" else "🔴"
    status_color = BotColors.SUCCESS if task["status"] == "open" else BotColors.ERROR
    
    embed = create_embed(
        f"{status_emoji} Volunteer Task #{task['id']}",
        f"**{task['title']}**",
        status_color
    )

    # Status with better formatting
    status_text = "Open for volunteers" if task["status"] == "open" else "Closed"
    embed.add_field(
        name="📊 Status",
        value=f"```{status_text}```",
        inline=True
    )

    embed.add_field(
        name="👤 Created By",
        value=f"```{task['creator_username']}```",
        inline=True
    )

    # Format date better
    created_date = task["created_at"]
    if hasattr(created_date, 'strftime'):
        date_str = created_date.strftime("%b %d, %Y at %H:%M")
    else:
        date_str = str(created_date)
    
    embed.add_field(
        name="📅 Created",
        value=f"```{date_str}```",
        inline=True
    )

    # Get participants count with better error handling
    try:
        from bot.core.database import db
        with db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM volunteer_participants WHERE task_id = %s" if db.mode == "postgres" else "SELECT COUNT(*) FROM volunteer_participants WHERE task_id = ?"
            cursor.execute(query, (task["id"],))
            count_result = cursor.fetchone()
            participants = count_result[0] if db.mode == "sqlite" else count_result["count"]
    except Exception:
        participants = 0

    embed.add_field(
        name="👥 Participants",
        value=f"```{participants} volunteers```",
        inline=True
    )

    return embed

def volunteer_tasks_list_embed(tasks: List[Dict[str, Any]]) -> discord.Embed:
    """Create an enhanced embed listing volunteer tasks."""
    embed = create_embed(
        "📋 Volunteer Tasks",
        f"Found **{len(tasks)}** volunteer tasks:",
        BotColors.INFO
    )

    if not tasks:
        embed.description = "No volunteer tasks available."
        embed.add_field(
            name="🚀 Get Started",
            value="Create the first task with `/volunteer add`!",
            inline=False
        )
        return embed

    for task in tasks[:10]:
        status_emoji = "🟢" if task["status"] == "open" else "🔴"
        created_date = task["created_at"].strftime("%b %d") if hasattr(task["created_at"], 'strftime') else str(task["created_at"])

        embed.add_field(
            name=f"{status_emoji} #{task['id']}: {task['title']}",
            value=f"**👤 Creator:** {task['creator_username']}\n**📊 Status:** {task['status'].title()}\n**📅 Created:** {created_date}",
            inline=False
        )

    if len(tasks) > 10:
        embed.set_footer(text=f"Showing 10 of {len(tasks)} tasks • Use /volunteer list to see all • Maximally : The global hackathon league")

    return embed

def team_info_embed(team_info: Dict[str, Any]) -> discord.Embed:
    """Create an enhanced team information embed."""
    owner_name = team_info.get('owner_name', team_info['owner'])
    
    embed = create_embed(
        f"👥 Team: {team_info['name']}",
        f"**🔑 Invite Code:** `{team_info['code']}`\n**👑 Owner:** {owner_name}",
        BotColors.PRIMARY
    )
    
    members = team_info.get('members', [])
    if members:
        # Format members list with better styling
        members_text = ""
        for i, member in enumerate(members, 1):
            crown = "👑 " if member == owner_name else f"{i}. "
            members_text += f"{crown}{member}\n"
        
        embed.add_field(
            name=f"👥 Members ({len(members)})",
            value=f"```{members_text.strip()}```",
            inline=False
        )
    else:
        embed.add_field(
            name="👥 Members",
            value="```No members yet```",
            inline=False
        )
    
    # Add helpful tips
    embed.add_field(
        name="💡 Team Tips",
        value="• Share your invite code with teammates\n• Use `/view-team` to check team status\n• Transfer ownership with `/transfer-team-ownership`",
        inline=False
    )
    
    return embed

def confirmation_embed(title: str, description: str, warning_text: str = None) -> discord.Embed:
    """Create a confirmation embed for destructive actions."""
    embed = create_embed(
        f"⚠️ {title}",
        description,
        BotColors.WARNING
    )
    
    if warning_text:
        embed.add_field(
            name="🚨 Warning",
            value=warning_text,
            inline=False
        )
    
    embed.add_field(
        name="⏰ Timeout",
        value="This confirmation will expire in 60 seconds.",
        inline=False
    )
    
    return embed

def help_embed(command_name: str, description: str, usage: str, examples: List[str] = None) -> discord.Embed:
    """Create a help embed for commands."""
    embed = create_embed(
        f"❓ Help: {command_name}",
        description,
        BotColors.INFO
    )
    
    embed.add_field(
        name="📝 Usage",
        value=f"```{usage}```",
        inline=False
    )
    
    if examples:
        examples_text = "\n".join([f"• `{example}`" for example in examples])
        embed.add_field(
            name="💡 Examples",
            value=examples_text,
            inline=False
        )
    
    return embed

class ConfirmationView(discord.ui.View):
    """Reusable confirmation view with consistent styling."""
    
    def __init__(self, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.confirmed = False
        self.cancelled = False
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancelled = True
        await interaction.response.edit_message(
            content="❌ Action cancelled.",
            embed=None,
            view=None
        )
        self.stop()

class PaginationView(discord.ui.View):
    """Reusable pagination view for long lists."""
    
    def __init__(self, embeds: List[discord.Embed], timeout: int = 300):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.max_pages = len(embeds)
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page."""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_pages - 1
        
        # Update page counter
        for item in self.children:
            if hasattr(item, 'label') and 'Page' in str(item.label):
                item.label = f"Page {self.current_page + 1}/{self.max_pages}"
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.primary, disabled=True)
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This button is just for display
        await interaction.response.defer()
    
    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)