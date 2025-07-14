"""
Configuration module for the Telegram bot.
"""
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for bot settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.topex_email = os.getenv("TOPEX_EMAIL")
        self.topex_password = os.getenv("TOPEX_PASSWORD")
        
        # Validate required environment variables
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        if not self.topex_email:
            raise ValueError("TOPEX_EMAIL environment variable is required")
            
        if not self.topex_password:
            raise ValueError("TOPEX_PASSWORD environment variable is required")
        
        # API settings
        self.topex_api_base = "https://lk.top-ex.ru/api"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.request_timeout = 30
        self.rate_limit_delay = 1  # seconds between API calls
        
        logger.info("Configuration loaded successfully")
