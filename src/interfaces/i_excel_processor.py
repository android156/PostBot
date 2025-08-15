"""
Интерфейс для обработчика Excel файлов.

Определяет контракт для всех классов, которые занимаются
обработкой и парсингом Excel документов с данными о маршрутах доставки.

Принципы SOLID:
- Interface Segregation Principle (ISP): Интерфейс содержит только необходимые методы
- Dependency Inversion Principle (DIP): Высокоуровневые модули зависят от абстракции
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IExcelProcessor(ABC):
    """
    Абстрактный интерфейс для обработки Excel файлов с маршрутами доставки.
    
    Этот интерфейс определяет единый контракт для всех классов,
    которые работают с Excel файлами, содержащими информацию о маршрутах доставки.
    """
    
    @abstractmethod
    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Обрабатывает Excel файл и извлекает данные о маршрутах доставки.
        
        Args:
            file_path (str): Путь к Excel файлу для обработки
            
        Returns:
            List[Dict[str, Any]]: Список словарей с данными о маршрутах.
                                  Каждый словарь содержит:
                                  - 'origin': город отправления
                                  - 'destination': город назначения
                                  - 'row_index': номер строки в Excel файле
                                  
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл имеет неправильный формат
            ExcelProcessingError: При ошибках обработки Excel файла
        """
        pass
        
    @abstractmethod
    def validate_file_format(self, file_path: str) -> bool:
        """
        Проверяет корректность формата Excel файла.
        
        Проверяет:
        - Наличие необходимых колонок (города отправления и назначения)
        - Правильность структуры файла
        - Наличие данных в файле
        
        Args:
            file_path (str): Путь к файлу для проверки
            
        Returns:
            bool: True если файл имеет корректный формат, False в противном случае
        """
        pass
        
    @abstractmethod
    def get_supported_column_names(self) -> Dict[str, List[str]]:
        """
        Возвращает список поддерживаемых названий колонок.
        
        Возвращает словарь с типами колонок и их возможными названиями
        для поддержки многоязычности и различных форматов файлов.
        
        Returns:
            Dict[str, List[str]]: Словарь с типами колонок:
                - 'origin': список возможных названий для колонки отправления
                - 'destination': список возможных названий для колонки назначения
        """
        pass