"""
Реализация генератора результатов.

Конкретная реализация интерфейса IResultGenerator для создания
Excel файлов с результатами расчета стоимости доставки.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за генерацию файлов
- Open/Closed Principle (OCP): Легко добавить поддержку новых форматов
- Dependency Inversion Principle (DIP): Реализует абстракцию
"""
import pandas as pd
import logging
import tempfile
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..interfaces.i_result_generator import IResultGenerator


logger = logging.getLogger(__name__)


class ExcelResultGenerator(IResultGenerator):
    """
    Конкретная реализация генератора Excel файлов с результатами.
    
    Создает форматированные Excel файлы с результатами расчета
    стоимости доставки, включая детальную информацию и сводки.
    """
    
    def __init__(self):
        """
        Инициализирует генератор результатов.
        """
        # Поддерживаемые форматы файлов
        self._supported_formats = ['xlsx', 'csv', 'json']
        
        # Стили для Excel файла
        self._excel_styles = {
            'header': {
                'font': {'bold': True, 'color': 'FFFFFF'},
                'fill': {'start_color': '366092', 'end_color': '366092', 'fill_type': 'solid'},
                'border': {'style': 'thin'},
                'alignment': {'horizontal': 'center', 'vertical': 'center'}
            },
            'data': {
                'border': {'style': 'thin'},
                'alignment': {'horizontal': 'left', 'vertical': 'center'}
            },
            'price': {
                'number_format': '#,##0.00 ₽',
                'border': {'style': 'thin'},
                'alignment': {'horizontal': 'right', 'vertical': 'center'}
            }
        }
        
        logger.info("ExcelResultGenerator инициализирован")
    
    def generate_result_file(
        self, 
        calculation_results: List[Dict[str, Any]],
        output_format: str = "xlsx"
    ) -> str:
        """
        Создает файл с результатами расчетов стоимости доставки.
        
        Args:
            calculation_results (List[Dict[str, Any]]): Результаты расчетов
            output_format (str): Формат выходного файла
            
        Returns:
            str: Путь к созданному файлу
        """
        if output_format not in self._supported_formats:
            raise ValueError(f"Неподдерживаемый формат: {output_format}")
        
        logger.info(f"Генерирую файл результатов в формате {output_format}")
        logger.info(f"Обрабатываю {len(calculation_results)} результатов расчетов")
        
        # Создаем временный файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f'.{output_format}',
            prefix=f'shipping_results_{timestamp}_'
        )
        temp_file.close()
        
        try:
            if output_format == 'xlsx':
                self._generate_excel_file(calculation_results, temp_file.name)
            elif output_format == 'csv':
                self._generate_csv_file(calculation_results, temp_file.name)
            elif output_format == 'json':
                self._generate_json_file(calculation_results, temp_file.name)
            
            logger.info(f"Файл результатов создан: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            # Удаляем временный файл при ошибке
            Path(temp_file.name).unlink(missing_ok=True)
            logger.error(f"Ошибка создания файла результатов: {e}")
            raise
    
    def get_supported_formats(self) -> List[str]:
        """
        Возвращает список поддерживаемых форматов файлов.
        
        Returns:
            List[str]: Список поддерживаемых форматов
        """
        return self._supported_formats.copy()
    
    def create_summary_sheet(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Создает сводку результатов для всех маршрутов.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            
        Returns:
            Dict[str, Any]: Сводная информация
        """
        if not results:
            return {
                'total_routes': 0,
                'successful_calculations': 0,
                'average_costs': {},
                'popular_companies': {}
            }
        
        total_routes = len(results)
        successful_calculations = sum(1 for r in results if r.get('is_successful', False))
        
        # Собираем все предложения для анализа
        all_offers = []
        for result in results:
            weight_results = result.get('weight_results', {})
            for weight_data in weight_results.values():
                offers = weight_data.get('offers', [])
                all_offers.extend(offers)
        
        # Рассчитываем средние стоимости по весам
        weight_costs = {}
        for offer in all_offers:
            weight = offer.get('weight', 0)
            price = offer.get('price', 0)
            
            if weight not in weight_costs:
                weight_costs[weight] = []
            weight_costs[weight].append(price)
        
        average_costs = {
            weight: sum(prices) / len(prices) 
            for weight, prices in weight_costs.items()
        }
        
        # Находим популярные компании
        company_counts = {}
        for offer in all_offers:
            company = offer.get('company_name', 'Неизвестная')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        # Сортируем компании по популярности
        popular_companies = dict(
            sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        summary = {
            'total_routes': total_routes,
            'successful_calculations': successful_calculations,
            'success_rate': (successful_calculations / total_routes * 100) if total_routes > 0 else 0,
            'total_offers': len(all_offers),
            'average_costs': average_costs,
            'popular_companies': popular_companies,
            'unique_companies': len(company_counts),
            'generation_time': datetime.now().isoformat()
        }
        
        logger.info(f"Создана сводка: {successful_calculations}/{total_routes} успешных расчетов")
        return summary
    
    def _generate_excel_file(self, results: List[Dict[str, Any]], file_path: str) -> None:
        """
        Генерирует Excel файл с результатами.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            file_path (str): Путь к файлу для создания
        """
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Создаем лист с общей сводкой
            summary = self.create_summary_sheet(results)
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Сводка', index=False)
            
            # Создаем основной лист с результатами
            main_data = self._prepare_main_data(results)
            main_df = pd.DataFrame(main_data)
            main_df.to_excel(writer, sheet_name='Результаты', index=False)
            
            # Создаем листы для каждой весовой категории
            weight_categories = self._get_weight_categories(results)
            for weight in weight_categories:
                weight_data = self._prepare_weight_data(results, weight)
                if weight_data:
                    weight_df = pd.DataFrame(weight_data)
                    sheet_name = f'Вес_{weight//1000}кг'
                    weight_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"Excel файл создан с {len(writer.sheets)} листами")
    
    def _generate_csv_file(self, results: List[Dict[str, Any]], file_path: str) -> None:
        """
        Генерирует CSV файл с результатами.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов  
            file_path (str): Путь к файлу для создания
        """
        main_data = self._prepare_main_data(results)
        df = pd.DataFrame(main_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        logger.info("CSV файл создан")
    
    def _generate_json_file(self, results: List[Dict[str, Any]], file_path: str) -> None:
        """
        Генерирует JSON файл с результатами.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            file_path (str): Путь к файлу для создания
        """
        import json
        
        output_data = {
            'summary': self.create_summary_sheet(results),
            'results': results,
            'generation_info': {
                'timestamp': datetime.now().isoformat(),
                'total_routes': len(results),
                'generator': 'ExcelResultGenerator'
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info("JSON файл создан")
    
    def _prepare_main_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Подготавливает основные данные для файла результатов.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            
        Returns:
            List[Dict[str, Any]]: Подготовленные данные
        """
        main_data = []
        
        for result in results:
            route_info = result.get('route', {})
            weight_results = result.get('weight_results', {})
            
            # Создаем строку для каждого веса
            for weight, weight_data in weight_results.items():
                cheapest_offer = weight_data.get('cheapest_offer')
                
                row = {
                    'Номер_строки': route_info.get('row_index', ''),
                    'Откуда': route_info.get('origin', ''),
                    'Куда': route_info.get('destination', ''),
                    'Вес_кг': weight / 1000,
                    'Статус': 'Успешно' if cheapest_offer else 'Ошибка',
                    'Компания': cheapest_offer.get('company_name', '') if cheapest_offer else '',
                    'Цена_руб': cheapest_offer.get('price', 0) if cheapest_offer else 0,
                    'Срок_дней': cheapest_offer.get('delivery_days', 0) if cheapest_offer else 0,
                    'Тариф': cheapest_offer.get('tariff_name', '') if cheapest_offer else '',
                    'Цена_за_кг': cheapest_offer.get('price_per_kg', 0) if cheapest_offer else 0,
                    'Количество_предложений': weight_data.get('offers_count', 0)
                }
                
                main_data.append(row)
        
        # Сортируем по номеру строки и весу
        main_data.sort(key=lambda x: (x.get('Номер_строки', 0), x.get('Вес_кг', 0)))
        
        return main_data
    
    def _prepare_weight_data(
        self, 
        results: List[Dict[str, Any]], 
        target_weight: int
    ) -> List[Dict[str, Any]]:
        """
        Подготавливает данные для конкретной весовой категории.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            target_weight (int): Целевой вес в граммах
            
        Returns:
            List[Dict[str, Any]]: Данные для веса
        """
        weight_data = []
        
        for result in results:
            route_info = result.get('route', {})
            weight_results = result.get('weight_results', {})
            
            if target_weight in weight_results:
                weight_result = weight_results[target_weight]
                offers = weight_result.get('offers', [])
                
                for offer in offers:
                    row = {
                        'Откуда': route_info.get('origin', ''),
                        'Куда': route_info.get('destination', ''),
                        'Компания': offer.get('company_name', ''),
                        'Цена_руб': offer.get('price', 0),
                        'Срок_дней': offer.get('delivery_days', 0),
                        'Тариф': offer.get('tariff_name', ''),
                        'Цена_за_кг': offer.get('price_per_kg', 0)
                    }
                    weight_data.append(row)
        
        # Сортируем по цене
        weight_data.sort(key=lambda x: x.get('Цена_руб', 0))
        
        return weight_data
    
    def _get_weight_categories(self, results: List[Dict[str, Any]]) -> List[int]:
        """
        Извлекает все использованные весовые категории.
        
        Args:
            results (List[Dict[str, Any]]): Результаты расчетов
            
        Returns:
            List[int]: Список весов в граммах
        """
        weights = set()
        
        for result in results:
            weight_results = result.get('weight_results', {})
            weights.update(weight_results.keys())
        
        return sorted(list(weights))