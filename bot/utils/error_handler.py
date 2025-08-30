import discord
import logging
from typing import Optional, Callable, Any
from functools import wraps
from .embed import error_embed, warning_embed, info_embed

logger = logging.getLogger(__name__)

class BotError(Exception):
    """Base exception for bot-specific errors."""
    def __init__(self, message: str, help_text: str = None, ephemeral: bool = True):
        self.message = message
        self.help_text = help_text
        self.ephemeral = ephemeral
        super().__init__(message)

class ValidationError(BotError):
    """Raised when user input validation fails."""
    pass

class ProfileNotFoundError(BotError):
    """Raised when a user profile is not found."""
    def __init__(self):
        super().__init__(
            "Profile Not Found",
            "Create your profile first using `/register-profile` to get started!"
        )

class TeamNotFoundError(BotError):
    """Raised when a team is not found."""
    def __init__(self, context: str = ""):
        help_text = "Use `/create-team` to create a new team or `/join-team` with a valid code."
        if context:
            help_text = f"{context} {help_text}"
        super().__init__(
            "Team Not Found",
            help_text
        )

class PermissionError(BotError):
    """Raised when user lacks required permissions."""
    def __init__(self, required_permission: str):
        super().__init__(
            "Insufficient Permissions",
            f"You need **{required_permission}** permission to use this command."
        )

class DatabaseError(BotError):
    """Raised when database operations fail."""
    def __init__(self):
        super().__init__(
            "Database Error",
            "Please try again in a few moments. If the issue persists, contact support."
        )

async def safe_send_response(
    interaction: discord.Interaction,
    content: str = None,
    embed: discord.Embed = None,
    view: discord.ui.View = None,
    ephemeral: bool = True,
    edit: bool = False
) -> Optional[discord.Message]:
    """Safely send a response, handling various interaction states."""
    try:
        if edit and interaction.response.is_done():
            return await interaction.edit_original_response(
                content=content,
                embed=embed,
                view=view
            )
        elif interaction.response.is_done():
            return await interaction.followup.send(
                content=content,
                embed=embed,
                view=view,
                ephemeral=ephemeral
            )
        else:
            return await interaction.response.send_message(
                content=content,
                embed=embed,
                view=view,
                ephemeral=ephemeral
            )
    except discord.errors.InteractionResponded:
        try:
            return await interaction.followup.send(
                content=content,
                embed=embed,
                view=view,
                ephemeral=ephemeral
            )
        except Exception as e:
            logger.error(f"Failed to send followup response: {e}")
            return None
    except discord.errors.NotFound:
        logger.warning("Interaction not found - user may have dismissed it")
        return None
    except Exception as e:
        logger.error(f"Failed to send response: {e}")
        return None

async def handle_error(
    interaction: discord.Interaction,
    error: Exception,
    command_name: str = "command"
) -> None:
    """Handle errors with appropriate user feedback."""
    
    if isinstance(error, BotError):
        # Custom bot errors with helpful messages
        embed = error_embed(
            error.message,
            help_text=error.help_text
        )
        await safe_send_response(
            interaction,
            embed=embed,
            ephemeral=error.ephemeral
        )
    elif isinstance(error, discord.errors.MissingPermissions):
        embed = error_embed(
            "Missing Permissions",
            f"You don't have permission to use this command.",
            help_text="Contact a server administrator if you believe this is an error."
        )
        await safe_send_response(interaction, embed=embed)
    elif isinstance(error, discord.errors.Forbidden):
        embed = error_embed(
            "Bot Permissions Error",
            "I don't have permission to perform this action.",
            help_text="Please ensure the bot has the necessary permissions in this server."
        )
        await safe_send_response(interaction, embed=embed)
    elif isinstance(error, ValueError):
        embed = error_embed(
            "Invalid Input",
            str(error),
            help_text=f"Check your input and try the `/{command_name}` command again."
        )
        await safe_send_response(interaction, embed=embed)
    else:
        # Generic error handling
        logger.error(f"Unhandled error in {command_name}: {error}", exc_info=True)
        embed = error_embed(
            "Something Went Wrong",
            "An unexpected error occurred while processing your request.",
            help_text="Please try again in a few moments. If the issue persists, contact support."
        )
        await safe_send_response(interaction, embed=embed)

def error_handler(command_name: str = None):
    """Decorator for automatic error handling in commands."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            try:
                return await func(self, interaction, *args, **kwargs)
            except Exception as error:
                cmd_name = command_name or func.__name__.replace('_', '-')
                await handle_error(interaction, error, cmd_name)
        return wrapper
    return decorator

async def defer_response(interaction: discord.Interaction, ephemeral: bool = True) -> bool:
    """Safely defer an interaction response."""
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=ephemeral)
            return True
    except discord.errors.InteractionResponded:
        pass
    except Exception as e:
        logger.warning(f"Failed to defer response: {e}")
    return False

def validate_profile_exists(func: Callable) -> Callable:
    """Decorator to check if user has a profile before executing command."""
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        from bot.core.database import db
        
        profile = db.get_profile(str(interaction.user.id))
        if not profile:
            raise ProfileNotFoundError()
        
        return await func(self, interaction, *args, **kwargs)
    return wrapper

def validate_team_membership(func: Callable) -> Callable:
    """Decorator to check if user is in a team before executing command."""
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        from bot.core.database import db
        
        team = db.get_team_by_member(str(interaction.user.id))
        if not team:
            raise TeamNotFoundError("You're not currently in a team.")
        
        return await func(self, interaction, *args, **kwargs)
    return wrapper

def validate_team_ownership(func: Callable) -> Callable:
    """Decorator to check if user owns their team before executing command."""
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        from bot.core.database import db
        
        team = db.get_team_by_member(str(interaction.user.id))
        if not team:
            raise TeamNotFoundError("You're not currently in a team.")
        
        if team["owner_id"] != str(interaction.user.id):
            raise PermissionError("team ownership")
        
        return await func(self, interaction, *args, **kwargs)
    return wrapper

async def send_success_message(
    interaction: discord.Interaction,
    title: str,
    description: str = None,
    ephemeral: bool = True
) -> None:
    """Send a standardized success message."""
    from .embed import success_embed
    
    embed = success_embed(title, description)
    await safe_send_response(interaction, embed=embed, ephemeral=ephemeral)

async def send_info_message(
    interaction: discord.Interaction,
    title: str,
    description: str = None,
    ephemeral: bool = True
) -> None:
    """Send a standardized info message."""
    embed = info_embed(title, description)
    await safe_send_response(interaction, embed=embed, ephemeral=ephemeral)

async def send_warning_message(
    interaction: discord.Interaction,
    title: str,
    description: str = None,
    ephemeral: bool = True
) -> None:
    """Send a standardized warning message."""
    embed = warning_embed(title, description)
    await safe_send_response(interaction, embed=embed, ephemeral=ephemeral)

class RateLimiter:
    """Simple rate limiter for commands."""
    def __init__(self):
        self.user_cooldowns = {}
    
    def is_on_cooldown(self, user_id: int, command: str, cooldown_seconds: int = 5) -> bool:
        """Check if user is on cooldown for a command."""
        import time
        
        key = f"{user_id}:{command}"
        current_time = time.time()
        
        if key in self.user_cooldowns:
            if current_time - self.user_cooldowns[key] < cooldown_seconds:
                return True
        
        self.user_cooldowns[key] = current_time
        return False
    
    def get_remaining_cooldown(self, user_id: int, command: str, cooldown_seconds: int = 5) -> float:
        """Get remaining cooldown time in seconds."""
        import time
        
        key = f"{user_id}:{command}"
        current_time = time.time()
        
        if key in self.user_cooldowns:
            elapsed = current_time - self.user_cooldowns[key]
            if elapsed < cooldown_seconds:
                return cooldown_seconds - elapsed
        
        return 0.0

# Global rate limiter instance
rate_limiter = RateLimiter()

# Export DatabaseError for use in other modules
__all__ = [
    'BotError', 'ValidationError', 'ProfileNotFoundError', 'TeamNotFoundError',
    'PermissionError', 'DatabaseError', 'safe_send_response', 'handle_error',
    'error_handler', 'defer_response', 'validate_profile_exists',
    'validate_team_membership', 'validate_team_ownership', 'send_success_message',
    'send_info_message', 'send_warning_message', 'cooldown', 'rate_limiter'
]

def cooldown(seconds: int = 5):
    """Decorator to add cooldown to commands."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            command_name = func.__name__
            user_id = interaction.user.id
            
            if rate_limiter.is_on_cooldown(user_id, command_name, seconds):
                remaining = rate_limiter.get_remaining_cooldown(user_id, command_name, seconds)
                embed = warning_embed(
                    "Slow Down!",
                    f"Please wait {remaining:.1f} seconds before using this command again.",
                )
                await safe_send_response(interaction, embed=embed)
                return
            
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator