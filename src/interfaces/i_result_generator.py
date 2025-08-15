"""
Интерфейс для генератора результатов.

Определяет контракт для классов, которые создают файлы с результатами
расчетов стоимости доставки в различных форматах.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за генерацию результатов
- Open/Closed Principle (OCP): Легко добавить новые форматы файлов
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import tempfile


class IResultGenerator(ABC):
    """
    Абстрактный интерфейс для генерации файлов с результатами расчетов.
    
    Позволяет создавать результирующие файлы в различных форматах
    на основе данных о расчете стоимости доставки.
    """
    
    @abstractmethod
    def generate_result_file(
        self, 
        calculation_results: List[Dict[str, Any]],
        output_format: str = "xlsx"
    ) -> str:
        """
        Создает файл с результатами расчетов стоимости доставки.
        
        Args:
            calculation_results (List[Dict[str, Any]]): Результаты расчетов.
                Каждый элемент содержит:
                - 'route': информация о маршруте
                - 'weight_categories': результаты для разных весов
                - 'cheapest_offers': самые выгодные предложения
                
            output_format (str): Формат выходного файла ('xlsx', 'csv', 'json')
            
        Returns:
            str: Путь к созданному файлу с результатами
            
        Raises:
            ResultGenerationError: При ошибке создания файла
            UnsupportedFormatError: При неподдерживаемом формате
        """
        pass
        
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Возвращает список поддерживаемых форматов файлов.
        
        Returns:
            List[str]: Список поддерживаемых форматов
        """
        pass
        
    @abstractmethod
    def create_summary_sheet(
        self, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Создает сводку результатов для всех маршрутов.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            
        Returns:
            Dict[str, Any]: Сводная информация:
                - 'total_routes': общее количество маршрутов
                - 'successful_calculations': успешные расчеты  
                - 'average_costs': средние стоимости по весам
                - 'popular_companies': часто встречающиеся компании
        """
        pass