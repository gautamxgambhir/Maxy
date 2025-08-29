import os
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord Configuration
    DISCORD_TOKEN: Optional[str] = os.getenv("DISCORD_TOKEN")
    GUILD_ID: Optional[int] = None
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    MAXIMALLY_LOGO_URL: Optional[str] = os.getenv("MAXIMALLY_LOGO_URL")

    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/profiles.db")

    # Email Configuration
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    EMAIL_FROM_ADDRESS: str = os.getenv("EMAIL_FROM_ADDRESS", "contact@maximally.in")
    EMAIL_DATABASE_URL: Optional[str] = os.getenv("EMAIL_DATABASE_URL")
    EMAIL_DATABASE_PATH: str = os.getenv("EMAIL_DATABASE_PATH", "data/email_assistant.db")

    # Security Configuration
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    ALLOWED_DOMAINS: list = os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else []

    def __init__(self):
        self._validate_configuration()

    def _validate_configuration(self):
        """Validate configuration values."""
        # Validate Discord token
        if self.DISCORD_TOKEN and len(self.DISCORD_TOKEN) < 50:
            raise ValueError("DISCORD_TOKEN appears to be invalid (too short)")

        # Validate GUILD_ID
        guild_id_str = os.getenv("GUILD_ID")
        if guild_id_str:
            try:
                self.GUILD_ID = int(guild_id_str)
                if self.GUILD_ID <= 0:
                    raise ValueError("GUILD_ID must be a positive integer")
            except ValueError:
                raise ValueError("GUILD_ID must be a valid integer")

        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.LOG_LEVEL not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")

        # Validate URLs
        if self.MAXIMALLY_LOGO_URL:
            if not self._is_valid_url(self.MAXIMALLY_LOGO_URL):
                raise ValueError("MAXIMALLY_LOGO_URL must be a valid HTTPS URL")

        if self.DATABASE_URL and not self._is_valid_database_url(self.DATABASE_URL):
            raise ValueError("DATABASE_URL format is invalid")

        if self.EMAIL_DATABASE_URL and not self._is_valid_database_url(self.EMAIL_DATABASE_URL):
            raise ValueError("EMAIL_DATABASE_URL format is invalid")

        # Validate email
        if not self._is_valid_email(self.EMAIL_FROM_ADDRESS):
            raise ValueError("EMAIL_FROM_ADDRESS must be a valid email address")

        # Ensure database paths are safe
        if not self._is_safe_path(self.DATABASE_PATH):
            raise ValueError("DATABASE_PATH contains unsafe characters")
        if not self._is_safe_path(self.EMAIL_DATABASE_PATH):
            raise ValueError("EMAIL_DATABASE_PATH contains unsafe characters")

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None

    def _is_valid_database_url(self, url: str) -> bool:
        """Validate database URL format."""
        # Allow PostgreSQL URLs or SQLite paths
        if url.startswith('postgresql://') or url.startswith('postgres://'):
            return True
        if url.endswith('.db') or url.endswith('.sqlite') or url.endswith('.sqlite3'):
            return True
        return False

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_safe_path(self, path: str) -> bool:
        """Check if file path is safe (no directory traversal)."""
        # Prevent directory traversal attacks
        if '..' in path or path.startswith('/'):
            return False
        # Allow alphanumeric, dots, slashes, underscores, hyphens
        pattern = r'^[a-zA-Z0-9._/-]+$'
        return re.match(pattern, path) is not None

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return not self.is_production

# Create global config instance
config = Config()
