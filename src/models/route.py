"""
Модель маршрута доставки.

Содержит класс для представления маршрута доставки
с информацией о городах отправления и назначения.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за данные маршрута
- Open/Closed Principle (OCP): Можно расширять новыми полями
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Route:
    """
    Модель маршрута доставки.
    
    Представляет один маршрут доставки с городами отправления и назначения.
    Используется во всей системе для передачи информации о маршрутах.
    
    Attributes:
        origin (str): Город или код города отправления
        destination (str): Город или код города назначения
        row_index (int): Номер строки в исходном Excel файле (для отчетности)
        origin_code (Optional[str]): Код города отправления в системе API
        destination_code (Optional[str]): Код города назначения в системе API
    """
    origin: str
    destination: str
    row_index: int
    origin_code: Optional[str] = None
    destination_code: Optional[str] = None
    
    def __post_init__(self):
        """
        Постобработка после инициализации объекта.
        
        Выполняет валидацию и нормализацию данных маршрута:
        - Удаляет лишние пробелы из названий городов
        - Проверяет, что города не пустые
        - Конвертирует номер строки в целое число
        """
        # Нормализация названий городов - удаляем лишние пробелы
        self.origin = self.origin.strip() if self.origin else ""
        self.destination = self.destination.strip() if self.destination else ""
        
        # Проверяем, что города указаны
        if not self.origin:
            raise ValueError("Город отправления не может быть пустым")
        if not self.destination:
            raise ValueError("Город назначения не может быть пустым")
            
        # Проверяем корректность номера строки
        if self.row_index < 0:
            raise ValueError("Номер строки не может быть отрицательным")
    
    def is_valid(self) -> bool:
        """
        Проверяет валидность маршрута.
        
        Returns:
            bool: True если маршрут корректен, False в противном случае
        """
        return (
            bool(self.origin.strip()) and 
            bool(self.destination.strip()) and 
            self.origin != self.destination and
            self.row_index >= 0
        )
    
    def has_city_codes(self) -> bool:
        """
        Проверяет, найдены ли коды городов для этого маршрута.
        
        Returns:
            bool: True если коды найдены для обоих городов
        """
        return bool(self.origin_code) and bool(self.destination_code)
    
    def get_display_name(self) -> str:
        """
        Возвращает читаемое представление маршрута.
        
        Returns:
            str: Строка вида "Москва → Санкт-Петербург"
        """
        return f"{self.origin} → {self.destination}"
    
    def to_dict(self) -> dict:
        """
        Конвертирует объект в словарь.
        
        Полезно для сериализации и передачи данных.
        
        Returns:
            dict: Словарь с данными маршрута
        """
        return {
            'origin': self.origin,
            'destination': self.destination,
            'row_index': self.row_index,
            'origin_code': self.origin_code,
            'destination_code': self.destination_code,
            'display_name': self.get_display_name(),
            'is_valid': self.is_valid(),
            'has_codes': self.has_city_codes()
        }