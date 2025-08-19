"""
Интерфейс для конфигурации приложения.

Определяет контракт для классов управления настройками и конфигурацией.
Позволяет легко менять источники конфигурации (файлы, переменные окружения, базы данных).

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за конфигурацию
- Open/Closed Principle (OCP): Открыт для расширения, закрыт для изменения
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IConfig(ABC):
    """
    Абстрактный интерфейс для управления конфигурацией приложения.
    
    Предоставляет единый способ доступа к настройкам приложения,
    независимо от источника конфигурации.
    """
    
    @abstractmethod
    def get_telegram_token(self) -> Optional[str]:
        """
        Возвращает токен Telegram бота.
        
        Returns:
            Optional[str]: Токен бота или None если не настроен
        """
        pass
        
    @abstractmethod
    def get_api_credentials(self) -> Dict[str, str]:
        """
        Возвращает учетные данные для API доставки.
        
        Returns:
            Dict[str, str]: Словарь с учетными данными:
                - 'email': электронная почта
                - 'password': пароль
                - 'base_url': базовый URL API
        """
        pass
        
    @abstractmethod
    def get_file_processing_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки для обработки файлов.
        
        Returns:
            Dict[str, Any]: Словарь с настройками:
                - 'max_file_size': максимальный размер файла в байтах
                - 'allowed_extensions': список разрешенных расширений
                - 'temp_dir': директория для временных файлов
        """
        pass
        
    @abstractmethod
    def get_api_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки для работы с API.
        
        Returns:
            Dict[str, Any]: Словарь с настройками:
                - 'timeout': таймаут запросов в секундах
                - 'retry_count': количество повторов при ошибке
                - 'rate_limit_delay': задержка между запросами
        """
        pass
        
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Проверяет корректность всех настроек конфигурации.
        
        Returns:
            bool: True если конфигурация корректна, False в противном случае
        """
        pass
        
    @abstractmethod
    def get_logging_settings(self) -> Dict[str, Any]:
        """
        Возвращает настройки логирования.
        
        Returns:
            Dict[str, Any]: Словарь с настройками логирования:
                - 'level': уровень логирования
                - 'file_path': путь к файлу логов
                - 'format': формат сообщений
                - 'max_file_size': максимальный размер файла логов
        """
        pass

    @abstractmethod
    def get_weight_categories(self) -> list[float]:
        """
        Возвращает список весовых категорий для тестирования.
        
        Returns:
            list[float]: Список весов в килограммах
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Возвращает всю конфигурацию в виде словаря.
        
        Returns:
            Dict[str, Any]: Словарь со всеми настройками
        """
        pass