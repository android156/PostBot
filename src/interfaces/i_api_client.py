"""
Интерфейс для клиентов внешних API.

Определяет общий контракт для всех классов, которые взаимодействуют
с внешними API для получения стоимости доставки.

Принципы SOLID:
- Single Responsibility Principle (SRP): Интерфейс отвечает только за API взаимодействие
- Interface Segregation Principle (ISP): Минимальный необходимый набор методов
- Dependency Inversion Principle (DIP): Абстракция для высокоуровневых модулей
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List


class IApiClient(ABC):
    """
    Абстрактный интерфейс для клиентов API доставки.
    
    Этот интерфейс определяет стандартные методы для работы
    с любыми API сервисами расчета стоимости доставки.
    """
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Выполняет аутентификацию в API.
        
        Этот метод должен получить токен авторизации или выполнить
        другие необходимые действия для доступа к API.
        
        Returns:
            bool: True если аутентификация успешна, False в противном случае
            
        Raises:
            AuthenticationError: При ошибке аутентификации
            NetworkError: При проблемах с сетью
        """
        pass
        
    @abstractmethod
    async def calculate_shipping_cost(
        self, 
        origin: str, 
        destination: str, 
        weight: int
    ) -> Dict[str, Any]:
        """
        Рассчитывает стоимость доставки для заданного маршрута и веса.
        
        Args:
            origin (str): Город или код города отправления
            destination (str): Город или код города назначения  
            weight (int): Вес груза в граммах
            
        Returns:
            Dict[str, Any]: Словарь с результатами расчета:
                - 'success': bool - успешность операции
                - 'offers': List[Dict] - список предложений от разных компаний
                - 'error': str - сообщение об ошибке (если есть)
                - 'cheapest_offer': Dict - самое дешевое предложение
                
        Raises:
            ApiError: При ошибках API
            ValidationError: При неверных входных данных
        """
        pass
        
    @abstractmethod
    async def get_available_cities(self) -> List[Dict[str, str]]:
        """
        Получает список доступных городов для доставки.
        
        Returns:
            List[Dict[str, str]]: Список словарей с информацией о городах:
                - 'code': код города в системе
                - 'name': название города
                - 'region': регион или область
                
        Raises:
            ApiError: При ошибках получения данных
        """
        pass
        
    @abstractmethod
    async def is_authenticated(self) -> bool:
        """
        Проверяет, есть ли действующая аутентификация.
        
        Returns:
            bool: True если есть валидная аутентификация, False в противном случае
        """
        pass
        
    @abstractmethod
    async def close(self) -> None:
        """
        Закрывает соединения и освобождает ресурсы.
        
        Этот метод должен вызываться при завершении работы
        для корректного освобождения сетевых ресурсов.
        """
        pass