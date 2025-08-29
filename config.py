import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD_ID = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID") else None
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAXIMALLY_LOGO_URL = os.getenv("MAXIMALLY_LOGO_URL")
    DATABASE_PATH = "data/profiles.db"
    
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "contact@maximally.in")
    EMAIL_DATABASE_PATH = "data/email_assistant.db"