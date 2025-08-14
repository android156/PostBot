#!/usr/bin/env python3
"""
Main entry point for the Telegram bot application.
"""
import logging
import sys
import asyncio
from bot import TelegramBot
from config import Config
from topex_api import TopExAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def initialize_api(config: Config) -> TopExAPI | None:
    """Initialize and pre-authenticate TOP-EX API client."""
    try:
        api = TopExAPI(config)
        if await api._ensure_authenticated():
            logger.info("TOP-EX API предварительно аутентифицирован")
            return api
        else:
            logger.error("Не удалось аутентифицироваться с TOP-EX API")
            return None
    except Exception as e:
        logger.error(f"Ошибка инициализации API: {e}")
        return None

def main():
    """Main function to start the bot."""
    logger.info("Запуск Telegram бота...")
    
    try:
        # Initialize configuration
        config = Config()
        logger.info("Конфигурация загружена успешно")
        
        # Pre-authenticate API client (будет выполнено при первом запросе)
        logger.info("API будет аутентифицирован при первом запросе")
        
        # Initialize bot
        bot = TelegramBot(config)
        logger.info("Бот инициализирован, начинаю опрос...")
        
        # Start bot with polling
        bot.application.run_polling(
            poll_interval=1.0,
            timeout=20,
            bootstrap_retries=3,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)