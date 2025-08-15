"""
Реализация процессора Excel файлов.

Конкретная реализация интерфейса IExcelProcessor для обработки
Excel файлов с данными о маршрутах доставки.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за обработку Excel
- Open/Closed Principle (OCP): Легко расширяется для новых форматов
- Dependency Inversion Principle (DIP): Зависит от абстракций
"""
import pandas as pd
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..interfaces.i_excel_processor import IExcelProcessor
from ..models.route import Route


logger = logging.getLogger(__name__)


class ExcelProcessor(IExcelProcessor):
    """
    Конкретная реализация процессора Excel файлов.
    
    Обрабатывает Excel файлы (.xlsx, .xls) и извлекает данные
    о маршрутах доставки для дальнейшего расчета стоимости.
    
    Поддерживает различные варианты названий колонок на русском и английском языках.
    """
    
    def __init__(self):
        """
        Инициализирует процессор Excel файлов.
        
        Настраивает поддерживаемые названия колонок и параметры обработки.
        """
        # Словарь поддерживаемых названий колонок (DRY принцип)
        self._column_names = {
            'origin': [
                'откуда', 'отправитель', 'город отправления', 'пункт отправления',
                'from', 'origin', 'departure', 'source', 'sender'
            ],
            'destination': [
                'куда', 'получатель', 'город назначения', 'пункт назначения', 
                'город доставки', 'адрес доставки',
                'to', 'destination', 'arrival', 'target', 'recipient'
            ]
        }
        
        # Настройки для pandas (принцип конфигурации)
        self._pandas_options = {
            'header': 0,  # Первая строка - заголовки
            'na_values': ['', ' ', 'N/A', 'NA', 'null', 'NULL'],  # Пустые значения
            'keep_default_na': True
        }
        
        logger.info("ExcelProcessor инициализирован")
    
    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Обрабатывает Excel файл и извлекает маршруты доставки.
        
        Args:
            file_path (str): Путь к Excel файлу
            
        Returns:
            List[Dict[str, Any]]: Список маршрутов с данными
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл имеет неправильный формат
        """
        logger.info(f"Начинаю обработку файла: {file_path}")
        
        # Проверяем существование файла
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        try:
            # Читаем Excel файл с обработкой ошибок
            df = self._read_excel_file(file_path)
            logger.info(f"Файл прочитан. Строк: {len(df)}, Колонок: {len(df.columns)}")
            
            # Находим нужные колонки
            origin_col, destination_col = self._find_required_columns(df)
            logger.info(f"Найдены колонки: '{origin_col}' и '{destination_col}'")
            
            # Извлекаем и валидируем данные маршрутов
            routes_data = self._extract_routes_data(df, origin_col, destination_col)
            
            logger.info(f"Успешно обработано {len(routes_data)} маршрутов из файла")
            return routes_data
            
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_path}: {e}")
            raise
    
    def validate_file_format(self, file_path: str) -> bool:
        """
        Проверяет корректность формата Excel файла.
        
        Args:
            file_path (str): Путь к файлу
            
        Returns:
            bool: True если формат корректен
        """
        try:
            # Проверяем расширение файла
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in ['.xlsx', '.xls']:
                logger.warning(f"Неподдерживаемое расширение файла: {file_extension}")
                return False
            
            # Пытаемся прочитать файл
            df = self._read_excel_file(file_path)
            
            # Проверяем наличие необходимых колонок
            origin_col, destination_col = self._find_required_columns(df)
            
            # Проверяем наличие данных
            if len(df) == 0:
                logger.warning("Файл не содержит данных")
                return False
                
            logger.info("Формат файла корректен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации файла: {e}")
            return False
    
    def get_supported_column_names(self) -> Dict[str, List[str]]:
        """
        Возвращает поддерживаемые названия колонок.
        
        Returns:
            Dict[str, List[str]]: Словарь с названиями колонок
        """
        return self._column_names.copy()  # Возвращаем копию для безопасности
    
    def _read_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        Читает Excel файл с правильными настройками.
        
        Приватный метод для чтения файла с обработкой различных форматов.
        
        Args:
            file_path (str): Путь к файлу
            
        Returns:
            pd.DataFrame: Данные из файла
        """
        file_extension = Path(file_path).suffix.lower()
        
        try:
            # Создаем копию опций для избежания конфликта с engine
            pandas_options = self._pandas_options.copy()
            
            if file_extension == '.xlsx':
                # Для .xlsx файлов используем openpyxl
                pandas_options['engine'] = 'openpyxl'
            else:
                # Для .xls файлов используем xlrd
                pandas_options['engine'] = 'xlrd'
            
            df = pd.read_excel(file_path, **pandas_options)
                
            # Удаляем полностью пустые строки
            df = df.dropna(how='all')
            
            # Приводим названия колонок к нижнему регистру для поиска
            df.columns = df.columns.astype(str).str.lower().str.strip()
            
            return df
            
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            raise ValueError(f"Не удалось прочитать Excel файл: {e}")
    
    def _find_required_columns(self, df: pd.DataFrame) -> tuple[str, str]:
        """
        Находит необходимые колонки в DataFrame.
        
        Ищет колонки с городами отправления и назначения
        по различным вариантам названий.
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            
        Returns:
            tuple[str, str]: Названия найденных колонок (отправление, назначение)
            
        Raises:
            ValueError: Если необходимые колонки не найдены
        """
        columns = df.columns.tolist()
        origin_col = None
        destination_col = None
        
        # Ищем колонку отправления
        for col_name in columns:
            if any(variant in col_name for variant in self._column_names['origin']):
                origin_col = col_name
                break
        
        # Ищем колонку назначения  
        for col_name in columns:
            if any(variant in col_name for variant in self._column_names['destination']):
                destination_col = col_name
                break
        
        # Проверяем, что найдены обе колонки
        if not origin_col:
            available_columns = ', '.join(columns)
            raise ValueError(
                f"Не найдена колонка с городом отправления. "
                f"Ожидаемые названия: {', '.join(self._column_names['origin'])}. "
                f"Доступные колонки: {available_columns}"
            )
        
        if not destination_col:
            available_columns = ', '.join(columns)
            raise ValueError(
                f"Не найдена колонка с городом назначения. "
                f"Ожидаемые названия: {', '.join(self._column_names['destination'])}. "
                f"Доступные колонки: {available_columns}"
            )
        
        return origin_col, destination_col
    
    def _extract_routes_data(
        self, 
        df: pd.DataFrame, 
        origin_col: str, 
        destination_col: str
    ) -> List[Dict[str, Any]]:
        """
        Извлекает данные маршрутов из DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame с данными
            origin_col (str): Название колонки отправления
            destination_col (str): Название колонки назначения
            
        Returns:
            List[Dict[str, Any]]: Список валидных маршрутов
        """
        routes_data = []
        
        for index, row in df.iterrows():
            try:
                # Получаем значения городов
                origin = str(row[origin_col]).strip() if pd.notna(row[origin_col]) else ""
                destination = str(row[destination_col]).strip() if pd.notna(row[destination_col]) else ""
                
                # Пропускаем пустые строки
                if not origin or not destination:
                    logger.debug(f"Пропускаем строку {index + 2}: пустые значения городов")
                    continue
                
                # Создаем объект маршрута для валидации
                route = Route(
                    origin=origin,
                    destination=destination,
                    row_index=int(index) + 2  # +2 потому что pandas index с 0, а Excel строки с 1, плюс заголовок
                )
                
                # Проверяем валидность маршрута
                if route.is_valid():
                    routes_data.append(route.to_dict())
                    logger.debug(f"Добавлен маршрут: {route.get_display_name()}")
                else:
                    logger.warning(f"Невалидный маршрут в строке {index + 2}: {origin} -> {destination}")
                    
            except Exception as e:
                logger.error(f"Ошибка обработки строки {index + 2}: {e}")
                continue
        
        if not routes_data:
            raise ValueError("В файле не найдено ни одного валидного маршрута")
        
        return routes_data