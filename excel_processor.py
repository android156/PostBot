"""
Excel file processor for extracting shipping route data.
"""
import pandas as pd
import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Processes Excel files containing shipping route data."""
    
    def __init__(self):
        """Initialize the Excel processor."""
        # Common column name patterns for different languages
        self.origin_patterns = [
            r'(откуда|отправитель|город.*отправ|from|origin|sender|отпр|пункт.*отправ)',
            r'(город.*1|city.*1|начальный|start)'
        ]
        
        self.destination_patterns = [
            r'(куда|получатель|город.*получ|to|destination|recipient|получ|пункт.*назначен)',
            r'(город.*2|city.*2|конечный|end)'
        ]
        
        self.weight_patterns = [
            r'(вес|масса|weight|кг|kg|г|g|mass)',
            r'(тонн|т|ton|pounds|lbs)'
        ]
        
    def process_file(self, file_path: str) -> List[Dict]:
        """
        Process Excel file and extract shipping route data.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List of dictionaries containing route data (without weight)
        """
        try:
            # Try to read Excel file
            df = pd.read_excel(file_path)
            
            if df.empty:
                raise ValueError("Файл пуст или не содержит данных")
                
            # Find relevant columns
            origin_col = self._find_column(df, self.origin_patterns)
            destination_col = self._find_column(df, self.destination_patterns)
            
            if not origin_col:
                raise ValueError("Не найдена колонка с городом отправления")
            if not destination_col:
                raise ValueError("Не найдена колонка с городом получения")
                
            logger.info(f"Found columns - Origin: {origin_col}, Destination: {destination_col}")
            
            # Extract and clean data
            routes = []
            for idx, (index, row) in enumerate(df.iterrows()):
                try:
                    origin = self._clean_city_name(str(row[origin_col]))
                    destination = self._clean_city_name(str(row[destination_col]))
                    
                    if origin and destination:
                        routes.append({
                            'origin': origin,
                            'destination': destination
                        })
                    else:
                        logger.warning(f"Skipping row {idx + 2}: invalid data")
                        
                except Exception as e:
                    logger.warning(f"Error processing row {idx + 2}: {e}")
                    continue
                    
            if not routes:
                raise ValueError("Не найдено валидных маршрутов в файле")
                
            logger.info(f"Successfully processed {len(routes)} routes")
            return routes
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise
            
    def _find_column(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """Find column by pattern matching."""
        columns = df.columns.tolist()
        
        for pattern in patterns:
            for col in columns:
                if re.search(pattern, str(col).lower()):
                    return col
                    
        return None
        
    def _clean_city_name(self, city: str) -> str:
        """Clean and normalize city name."""
        if not city or city.lower() in ['nan', 'none', '']:
            return ""
            
        # Remove extra whitespace
        city = city.strip()
        
        # Remove common prefixes
        city = re.sub(r'^(г\.?\s*|город\s*|city\s*)', '', city, flags=re.IGNORECASE)
        
        # Remove postal codes at the beginning
        city = re.sub(r'^\d{5,6}\s*,?\s*', '', city)
        
        return city
        
    def _parse_weight(self, weight_str: str) -> int:
        """Parse weight from string and convert to grams."""
        if not weight_str or weight_str.lower() in ['nan', 'none', '']:
            return 0
            
        # Remove non-numeric characters except decimal point
        weight_str = re.sub(r'[^\d.,]', '', weight_str)
        
        if not weight_str:
            return 0
            
        # Replace comma with dot for decimal parsing
        weight_str = weight_str.replace(',', '.')
        
        try:
            weight = float(weight_str)
            
            # Determine if it's in kg or grams based on value
            if weight < 50:  # Assume kg if less than 50
                weight = weight * 1000  # Convert to grams
                
            return int(weight)
            
        except ValueError:
            logger.warning(f"Could not parse weight: {weight_str}")
            return 0
