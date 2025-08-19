"""
Реализация менеджера конфигурации.

Конкретная реализация интерфейса IConfig для управления
настройками приложения из переменных окружения.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за конфигурацию
- Open/Closed Principle (OCP): Легко добавлять новые настройки
- Dependency Inversion Principle (DIP): Реализует абстрактный интерфейс
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..interfaces.i_config import IConfig

logger = logging.getLogger(__name__)


class ConfigManager(IConfig):
    """
    Конкретная реализация менеджера конфигурации.
    
    Загружает настройки из переменных окружения и предоставляет
    их в удобном формате для других компонентов системы.
    
    Поддерживает валидацию настроек и значения по умолчанию.
    """

    def __init__(self):
        """
        Инициализирует менеджер конфигурации.
        
        Загружает все настройки из переменных окружения
        и проверяет их корректность.
        """
        # Настройки по умолчанию (принцип DRY)
        self._default_settings = {
            'api_timeout': 150,
            'max_file_size': 10 * 1024 * 1024,  # 10 MB
            'retry_count': 3,
            'rate_limit_delay': 1.0,
            'temp_dir': '/tmp',
            'log_level': 'INFO',
            'log_file': 'bot.log',
            'max_log_file_size': 50 * 1024 * 1024,  # 50 MB
            'topex_api_base': 'https://lk.top-ex.ru/api',
            # Весовые категории по умолчанию в килограммах
            'weight_categories': [0.5, 1.0, 5.0, 10.0, 20.0, 30.0, ],
            # 'weight_categories': [0.5, 1],
            # Статичные параметры API TOP-EX
            'topex_user_id': '14',
            # 'topex_cargo_type': '4aab1fc6-fc2b-473a-8728-58bcd4ff79ba',  # "груз"
            'topex_cargo_type':
            '81dd8a13-8235-494f-84fd-9c04c51d50ec',  # "документы
            'topex_cargo_seats_number': '1',
            'topex_delivery_method': '1',  # 1 = доставка до дверей
            # Фильтр категорий доставки (пустой список = без фильтрации)
            'delivery_filter':
            ['До дверей']  # Например: ['До дверей', 'Дверь - Склад']
        }

        # Загружаем настройки
        self._load_configuration()

        logger.info("ConfigManager инициализирован и настройки загружены")

    def get_telegram_token(self) -> Optional[str]:
        """
        Возвращает токен Telegram бота.
        
        Returns:
            Optional[str]: Токен бота или None если не настроен
        """
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return token

    def get_api_credentials(self) -> Dict[str, str]:
        """
        Возвращает учетные данные для TOP-EX API.
        
        Returns:
            Dict[str, str]: Словарь с учетными данными
        """
        credentials = {
            'email':
            os.getenv('TOPEX_EMAIL', ''),
            'password':
            os.getenv('TOPEX_PASSWORD', ''),
            'base_url':
            os.getenv('TOPEX_API_BASE',
                      self._default_settings['topex_api_base'])
        }

        # Проверяем наличие обязательных учетных данных
        if not credentials['email']:
            logger.error("TOPEX_EMAIL не найден в переменных окружения")
        if not credentials['password']:
            logger.error("TOPEX_PASSWORD не найден в переменных окружения")

        return credentials

    def get_file_processing_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки для обработки файлов.
        
        Returns:
            Dict[str, Any]: Настройки обработки файлов
        """
        return {
            'max_file_size':
            int(
                os.getenv('MAX_FILE_SIZE',
                          str(self._default_settings['max_file_size']))),
            'allowed_extensions': ['.xlsx', '.xls'],
            'temp_dir':
            os.getenv('TEMP_DIR', self._default_settings['temp_dir'])
        }

    def get_api_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки для работы с API.
        
        Returns:
            Dict[str, Any]: Настройки API
        """
        return {
            'timeout':
            int(
                os.getenv('API_TIMEOUT',
                          str(self._default_settings['api_timeout']))),
            'retry_count':
            int(
                os.getenv('RETRY_COUNT',
                          str(self._default_settings['retry_count']))),
            'rate_limit_delay':
            float(
                os.getenv('RATE_LIMIT_DELAY',
                          str(self._default_settings['rate_limit_delay'])))
        }

    def validate_configuration(self) -> bool:
        """
        Проверяет корректность всех настроек конфигурации.
        
        Returns:
            bool: True если конфигурация корректна
        """
        is_valid = True
        validation_errors = []

        # Проверяем токен Telegram
        if not self.get_telegram_token():
            is_valid = False
            validation_errors.append(
                "Отсутствует токен Telegram бота (TELEGRAM_BOT_TOKEN)")

        # Проверяем учетные данные API
        api_credentials = self.get_api_credentials()
        if not api_credentials['email']:
            is_valid = False
            validation_errors.append(
                "Отсутствует email для TOP-EX API (TOPEX_EMAIL)")
        if not api_credentials['password']:
            is_valid = False
            validation_errors.append(
                "Отсутствует пароль для TOP-EX API (TOPEX_PASSWORD)")

        # Проверяем настройки файлов
        file_settings = self.get_file_processing_settings()
        if file_settings['max_file_size'] <= 0:
            is_valid = False
            validation_errors.append("Неверный максимальный размер файла")

        # Проверяем настройки API
        api_settings = self.get_api_settings()
        if api_settings['timeout'] <= 0:
            is_valid = False
            validation_errors.append("Неверный таймаут API")
        if api_settings['retry_count'] < 0:
            is_valid = False
            validation_errors.append("Неверное количество повторов")

        # Проверяем директорию для временных файлов
        temp_dir = Path(file_settings['temp_dir'])
        if not temp_dir.exists():
            try:
                temp_dir.mkdir(parents=True, exist_ok=True)
                logger.info(
                    f"Создана директория для временных файлов: {temp_dir}")
            except Exception as e:
                is_valid = False
                validation_errors.append(
                    f"Не удалось создать временную директорию: {e}")

        # Логируем ошибки валидации
        if validation_errors:
            for error in validation_errors:
                logger.error(f"Ошибка конфигурации: {error}")
        else:
            logger.info("Конфигурация прошла валидацию успешно")

        return is_valid

    def get_logging_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки логирования.
        
        Returns:
            Dict[str, Any]: Настройки логирования
        """
        return {
            'level':
            os.getenv('LOG_LEVEL', self._default_settings['log_level']),
            'file_path':
            os.getenv('LOG_FILE', self._default_settings['log_file']),
            'format':
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'max_file_size':
            int(
                os.getenv('MAX_LOG_FILE_SIZE',
                          str(self._default_settings['max_log_file_size'])))
        }

    def get_weight_categories(self) -> list[float]:
        """
        Возвращает список весовых категорий для тестирования.
        
        Дополнительный метод для получения весовых категорий,
        используемых при расчете стоимости доставки.
        
        Returns:
            list[float]: Список весов в килограммах
        """
        # Веса по умолчанию в кг (можно настроить через переменную окружения)
        default_weights = self._default_settings['weight_categories']

        weight_categories_str = os.getenv('WEIGHT_CATEGORIES', '')
        if weight_categories_str:
            try:
                # Парсим веса из строки вида "0.5,1.0,2.0,5.0,10.0"
                weights = [
                    float(w.strip()) for w in weight_categories_str.split(',')
                ]
                logger.info(
                    f"Используются настраиваемые весовые категории: {weights}")
                return weights
            except ValueError as e:
                logger.warning(
                    f"Ошибка парсинга весовых категорий: {e}. Используются значения по умолчанию"
                )

        logger.info(
            f"Используются весовые категории по умолчанию: {default_weights}")
        return default_weights

    def get_api_parameters(self) -> Dict[str, str]:
        """
        Возвращает статичные параметры для запросов к TOP-EX API.
        
        Returns:
            Dict[str, str]: Словарь с параметрами API
        """
        return {
            'user_id':
            os.getenv('TOPEX_USER_ID',
                      self._default_settings['topex_user_id']),
            'cargo_type':
            os.getenv('TOPEX_CARGO_TYPE',
                      self._default_settings['topex_cargo_type']),
            'cargo_seats_number':
            os.getenv('TOPEX_CARGO_SEATS_NUMBER',
                      self._default_settings['topex_cargo_seats_number']),
            'delivery_method':
            os.getenv('TOPEX_DELIVERY_METHOD',
                      self._default_settings['topex_delivery_method'])
        }

    def _load_configuration(self) -> None:
        """
        Загружает конфигурацию из переменных окружения.
        
        Приватный метод для инициализации всех настроек
        при создании объекта конфигурации.
        """
        logger.info("Загружаю конфигурацию из переменных окружения...")

        # Логируем найденные переменные окружения (без секретных данных)
        env_vars = {
            'TELEGRAM_BOT_TOKEN': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'TOPEX_EMAIL': bool(os.getenv('TOPEX_EMAIL')),
            'TOPEX_PASSWORD': bool(os.getenv('TOPEX_PASSWORD')),
            'TOPEX_API_BASE': os.getenv('TOPEX_API_BASE', 'default'),
            'MAX_FILE_SIZE': os.getenv('MAX_FILE_SIZE', 'default'),
            'API_TIMEOUT': os.getenv('API_TIMEOUT', 'default'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'default')
        }

        logger.info(f"Статус переменных окружения: {env_vars}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Возвращает всю конфигурацию в виде словаря.
        
        Полезно для отладки и логирования конфигурации.
        
        Returns:
            Dict[str, Any]: Словарь со всеми настройками (без секретных данных)
        """
        config = {
            'telegram_token_set': bool(self.get_telegram_token()),
            'api_credentials': {
                'email_set': bool(self.get_api_credentials()['email']),
                'password_set': bool(self.get_api_credentials()['password']),
                'base_url': self.get_api_credentials()['base_url']
            },
            'file_processing': self.get_file_processing_settings(),
            'api_settings': self.get_api_settings(),
            'logging': self.get_logging_settings(),
            'weight_categories': self.get_weight_categories(),
            'api_parameters': self.get_api_parameters(),
            'delivery_filter': self.get_delivery_filter(),
            'is_valid': self.validate_configuration()
        }

        return config

    def get_delivery_filter(self) -> list[str]:
        """
        Возвращает список разрешенных типов доставки для фильтрации.
        
        Если список пустой, фильтрация не применяется.
        
        Returns:
            list[str]: Список разрешенных типов доставки
        """
        # Фильтр по умолчанию
        default_filter = self._default_settings['delivery_filter']

        delivery_filter_str = os.getenv('DELIVERY_FILTER', '')
        if delivery_filter_str:
            try:
                # Парсим фильтр из строки вида "До дверей,Дверь - Склад,Склад - Дверь"
                filter_list = [
                    f.strip() for f in delivery_filter_str.split(',')
                    if f.strip()
                ]
                logger.info(
                    f"Используется настраиваемый фильтр доставки: {filter_list}"
                )
                return filter_list
            except ValueError as e:
                logger.warning(
                    f"Ошибка парсинга фильтра доставки: {e}. Используются значения по умолчанию"
                )

        if default_filter:
            logger.info(
                f"Используется фильтр доставки по умолчанию: {default_filter}")
        else:
            logger.info(
                "Фильтр доставки не настроен (все предложения проходят)")

        return default_filter
