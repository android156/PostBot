"""
Главный модуль приложения.

Точка входа в приложение Telegram бота для расчета стоимости доставки.
Инициализирует все компоненты системы с использованием принципов SOLID.

Принципы SOLID:
- Dependency Inversion Principle (DIP): Использует внедрение зависимостей
- Single Responsibility Principle (SRP): Отвечает только за инициализацию
- Open/Closed Principle (OCP): Легко добавлять новые компоненты
"""
import logging
import sys
import asyncio
from pathlib import Path

# Добавляем путь к модулям в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

# Импорты интерфейсов
from src.interfaces.i_config import IConfig
from src.interfaces.i_excel_processor import IExcelProcessor
from src.interfaces.i_api_client import IApiClient
from src.interfaces.i_result_generator import IResultGenerator
from src.interfaces.i_bot_service import IBotService

# Импорты реализаций
from src.implementations.config_manager import ConfigManager
from src.implementations.excel_processor import ExcelProcessor
from src.implementations.topex_api_client import TopExApiClient
from src.implementations.result_generator import ExcelResultGenerator

# Импорт сервиса
from src.services.bot_service import BotService

# Импорты Telegram Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters


class ApplicationContainer:
    """
    Контейнер для внедрения зависимостей (Dependency Injection Container).
    
    Создает и настраивает все компоненты приложения согласно принципам SOLID.
    Обеспечивает слабую связанность между компонентами.
    """
    
    def __init__(self):
        """
        Инициализирует контейнер и создает все зависимости.
        """
        self._logger = logging.getLogger(__name__)
        self._components = {}
        
        # Создаем компоненты в правильном порядке зависимостей
        self._create_components()
        
        self._logger.info("ApplicationContainer инициализирован со всеми зависимостями")
    
    def _create_components(self) -> None:
        """
        Создает все компоненты приложения.
        
        Порядок создания важен из-за зависимостей между компонентами.
        """
        # 1. Конфигурация (не зависит от других компонентов)
        self._components['config'] = self._create_config()
        
        # 2. Процессор Excel (не зависит от других компонентов)
        self._components['excel_processor'] = self._create_excel_processor()
        
        # 3. API клиент (зависит от конфигурации)
        self._components['api_client'] = self._create_api_client()
        
        # 4. Генератор результатов (не зависит от других компонентов)
        self._components['result_generator'] = self._create_result_generator()
        
        # 5. Сервис бота (зависит от всех предыдущих компонентов)
        self._components['bot_service'] = self._create_bot_service()
        
        self._logger.info("Все компоненты приложения созданы успешно")
    
    def _create_config(self) -> IConfig:
        """
        Создает компонент конфигурации.
        
        Returns:
            IConfig: Реализация интерфейса конфигурации
        """
        try:
            config = ConfigManager()
            
            # Валидируем конфигурацию при создании
            if not config.validate_configuration():
                self._logger.error("Конфигурация содержит ошибки")
                raise ValueError("Неверная конфигурация приложения")
            
            self._logger.info("Компонент конфигурации создан и проверен")
            return config
            
        except Exception as e:
            self._logger.error(f"Ошибка создания компонента конфигурации: {e}")
            raise
    
    def _create_excel_processor(self) -> IExcelProcessor:
        """
        Создает компонент обработки Excel файлов.
        
        Returns:
            IExcelProcessor: Реализация интерфейса обработки Excel
        """
        try:
            excel_processor = ExcelProcessor()
            self._logger.info("Компонент обработки Excel создан")
            return excel_processor
            
        except Exception as e:
            self._logger.error(f"Ошибка создания компонента Excel: {e}")
            raise
    
    def _create_api_client(self) -> IApiClient:
        """
        Создает компонент API клиента.
        
        Returns:
            IApiClient: Реализация интерфейса API клиента
        """
        try:
            config = self._components['config']
            api_client = TopExApiClient(config)
            self._logger.info("Компонент API клиента создан")
            return api_client
            
        except Exception as e:
            self._logger.error(f"Ошибка создания API клиента: {e}")
            raise
    
    def _create_result_generator(self) -> IResultGenerator:
        """
        Создает компонент генерации результатов.
        
        Returns:
            IResultGenerator: Реализация интерфейса генерации результатов
        """
        try:
            result_generator = ExcelResultGenerator()
            self._logger.info("Компонент генерации результатов создан")
            return result_generator
            
        except Exception as e:
            self._logger.error(f"Ошибка создания генератора результатов: {e}")
            raise
    
    def _create_bot_service(self) -> IBotService:
        """
        Создает основной сервис бота.
        
        Returns:
            IBotService: Реализация интерфейса сервиса бота
        """
        try:
            # Получаем все необходимые зависимости
            config = self._components['config']
            excel_processor = self._components['excel_processor']
            api_client = self._components['api_client']
            result_generator = self._components['result_generator']
            
            # Создаем сервис с внедрением зависимостей
            bot_service = BotService(
                config=config,
                excel_processor=excel_processor,
                api_client=api_client,
                result_generator=result_generator
            )
            
            self._logger.info("Сервис бота создан со всеми зависимостями")
            return bot_service
            
        except Exception as e:
            self._logger.error(f"Ошибка создания сервиса бота: {e}")
            raise
    
    def get_bot_service(self) -> IBotService:
        """
        Возвращает основной сервис бота.
        
        Returns:
            IBotService: Настроенный сервис бота
        """
        return self._components['bot_service']
    
    def get_config(self) -> IConfig:
        """
        Возвращает компонент конфигурации.
        
        Returns:
            IConfig: Компонент конфигурации
        """
        return self._components['config']
    
    async def cleanup(self) -> None:
        """
        Освобождает ресурсы всех компонентов.
        
        Вызывает методы очистки для компонентов, которые их поддерживают.
        """
        try:
            self._logger.info("Начинаю освобождение ресурсов компонентов...")
            
            # Останавливаем сервис бота
            if 'bot_service' in self._components:
                await self._components['bot_service'].stop_bot()
            
            # Закрываем API клиент
            if 'api_client' in self._components:
                await self._components['api_client'].close()
            
            self._logger.info("Все ресурсы компонентов освобождены")
            
        except Exception as e:
            self._logger.error(f"Ошибка при освобождении ресурсов: {e}")


def setup_logging(config: IConfig) -> None:
    """
    Настраивает систему логирования приложения.
    
    Args:
        config (IConfig): Конфигурация приложения
    """
    try:
        log_settings = config.get_logging_settings()
        
        # Настройка форматтера
        formatter = logging.Formatter(log_settings['format'])
        
        # Настройка корневого логгера
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_settings['level']))
        
        # Очищаем существующие обработчики
        root_logger.handlers.clear()
        
        # Добавляем обработчик для файла
        file_handler = logging.FileHandler(log_settings['file_path'], encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Добавляем обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        logging.info(f"Система логирования настроена. Уровень: {log_settings['level']}")
        
    except Exception as e:
        print(f"Ошибка настройки логирования: {e}")
        raise


async def main():
    """
    Главная асинхронная функция приложения.
    
    Инициализирует все компоненты и запускает основной цикл работы бота.
    """
    container = None
    
    try:
        # Создаем контейнер зависимостей
        container = ApplicationContainer()
        
        # Настраиваем логирование
        config = container.get_config()
        setup_logging(config)
        
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("Запуск Telegram бота для расчета стоимости доставки")
        logger.info("=" * 60)
        
        # Логируем информацию о конфигурации (без секретных данных)
        config_info = config.to_dict()
        logger.info("Конфигурация приложения:")
        for key, value in config_info.items():
            if key != 'weight_categories':  # Выводим веса отдельно
                logger.info(f"  {key}: {value}")
        
        weight_categories = config.get_weight_categories()
        weight_kg = [f"{w:.1f}кг" for w in weight_categories]
        logger.info(f"  Весовые категории: {', '.join(weight_kg)}")
        
        # Получаем сервис бота
        bot_service = container.get_bot_service()
        
        # Запускаем сервис бота
        await bot_service.start_bot()
        
        logger.info("Приложение успешно запущено и готово к работе")
        logger.info("Для остановки нажмите Ctrl+C")
        
        # Получаем токен Telegram из конфигурации
        telegram_token = config.get_telegram_token()
        
        # Создаем Telegram Application
        application = Application.builder().token(telegram_token).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", bot_service.handle_start_command))
        application.add_handler(CommandHandler("help", bot_service.handle_help_command))
        
        # Регистрируем обработчик документов
        application.add_handler(MessageHandler(filters.Document.ALL, bot_service.handle_document))
        
        # Регистрируем обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_service.handle_text_message))
        
        logger.info("Telegram бот запускается...")
        
        # Запускаем бота
        await application.run_polling()
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки от пользователя")
        
    except Exception as e:
        logger.error(f"Критическая ошибка приложения: {e}")
        sys.exit(1)
        
    finally:
        # Освобождаем ресурсы
        if container:
            try:
                await container.cleanup()
            except Exception as e:
                logger.error(f"Ошибка при освобождении ресурсов: {e}")
        
        logger.info("Приложение завершено")


def run():
    """
    Функция запуска приложения.
    
    Обеспечивает правильную обработку исключений и сигналов завершения.
    """
    try:
        # Запускаем главную асинхронную функцию
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nПриложение остановлено пользователем")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()