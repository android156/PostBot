"""
Интерфейс для службы Telegram бота.

Определяет контракт для основной логики работы бота,
обработки команд и сообщений пользователей.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за логику бота
- Interface Segregation Principle (ISP): Только необходимые методы
- Dependency Inversion Principle (DIP): Абстракция для высокоуровневой логики
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from telegram import Update
from telegram.ext import ContextTypes


class IBotService(ABC):
    """
    Абстрактный интерфейс для службы Telegram бота.
    
    Определяет основные методы для обработки команд и сообщений
    пользователей в Telegram боте.
    """
    
    @abstractmethod
    async def handle_start_command(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обрабатывает команду /start.
        
        Отправляет приветственное сообщение новому пользователю
        с инструкциями по использованию бота.
        
        Args:
            update (Update): Объект обновления от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        pass
        
    @abstractmethod
    async def handle_help_command(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обрабатывает команду /help.
        
        Отправляет подробную справку по использованию бота,
        включая требования к формату файлов и примеры.
        
        Args:
            update (Update): Объект обновления от Telegram
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        pass
        
    @abstractmethod
    async def handle_document(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обрабатывает загруженные документы (Excel файлы).
        
        Проверяет формат файла, обрабатывает данные о маршрутах,
        рассчитывает стоимость доставки и отправляет результат пользователю.
        
        Args:
            update (Update): Объект обновления от Telegram с документом
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        pass
        
    @abstractmethod
    async def handle_text_message(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Обрабатывает текстовые сообщения от пользователей.
        
        Реагирует на текстовые сообщения, которые не являются командами,
        предоставляя помощь или перенаправляя к нужной функциональности.
        
        Args:
            update (Update): Объект обновления от Telegram с текстом
            context (ContextTypes.DEFAULT_TYPE): Контекст бота
        """
        pass
        
    @abstractmethod
    async def process_shipping_calculation(
        self, 
        routes_data: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Выполняет расчет стоимости доставки для списка маршрутов.
        
        Принимает данные о маршрутах и возвращает результаты расчета
        для разных весовых категорий с самыми выгодными предложениями.
        
        Args:
            routes_data (list[Dict[str, Any]]): Список маршрутов для расчета
            
        Returns:
            Dict[str, Any]: Результаты расчета:
                - 'success': bool - успешность операции
                - 'results': List[Dict] - результаты для каждого маршрута
                - 'summary': Dict - общая сводка
                - 'error': str - сообщение об ошибке (если есть)
        """
        pass
        
    @abstractmethod
    async def start_bot(self) -> None:
        """
        Запускает бота и начинает опрос обновлений.
        
        Инициализирует соединение с Telegram API и начинает
        обработку входящих сообщений от пользователей.
        """
        pass
        
    @abstractmethod
    async def stop_bot(self) -> None:
        """
        Останавливает бота и освобождает ресурсы.
        
        Корректно завершает работу бота, закрывает соединения
        и освобождает все используемые ресурсы.
        """
        pass