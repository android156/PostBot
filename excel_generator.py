"""
Excel file generator for shipping cost calculation results.
"""
import pandas as pd
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelGenerator:
    """Generates Excel files with shipping cost results."""
    
    def __init__(self):
        """Initialize the Excel generator."""
        pass
    
    def generate_results_file(self, results: List[Dict], output_path: str) -> str:
        """
        Generate Excel file with shipping cost results.
        
        Args:
            results: List of route results with costs for different weights
            output_path: Path where to save the Excel file
            
        Returns:
            Path to the generated Excel file
        """
        try:
            # Prepare data for Excel
            excel_data = []
            
            for route_result in results:
                route_origin = route_result.get('origin', '')
                route_destination = route_result.get('destination', '')
                
                # Get weight results
                weight_results = route_result.get('weight_results', {})
                
                for weight, weight_data in weight_results.items():
                    if weight_data.get('error'):
                        # Add error row
                        excel_data.append({
                            'Откуда': route_origin,
                            'Куда': route_destination,
                            'Вес (кг)': weight / 1000,  # Convert grams to kg
                            'Компания': 'ОШИБКА',
                            'Цена (руб.)': '-',
                            'Срок (дн.)': '-',
                            'Комментарий': weight_data.get('error', '')
                        })
                    else:
                        # Find cheapest offer
                        cheapest = weight_data.get('cheapest_offer')
                        if cheapest:
                            excel_data.append({
                                'Откуда': route_origin,
                                'Куда': route_destination,
                                'Вес (кг)': weight / 1000,  # Convert grams to kg
                                'Компания': cheapest.get('company', ''),
                                'Цена (руб.)': cheapest.get('price', 0),
                                'Срок (дн.)': cheapest.get('delivery_days', ''),
                                'Комментарий': cheapest.get('tariff', '')
                            })
                        else:
                            # No offers found
                            excel_data.append({
                                'Откуда': route_origin,
                                'Куда': route_destination,
                                'Вес (кг)': weight / 1000,
                                'Компания': 'НЕТ ПРЕДЛОЖЕНИЙ',
                                'Цена (руб.)': '-',
                                'Срок (дн.)': '-',
                                'Комментарий': 'Нет доступных предложений'
                            })
            
            # Create DataFrame
            df = pd.DataFrame(excel_data)
            
            if df.empty:
                raise ValueError("Нет данных для создания Excel файла")
            
            # Save to Excel with formatting
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Результаты', index=False)
                
                # Get the workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Результаты']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Excel file generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Excel file: {e}")
            raise
    
    def format_weight_display(self, weight_grams: int) -> str:
        """Format weight for display in Excel."""
        if weight_grams >= 1000:
            return f"{weight_grams / 1000:.1f} кг"
        else:
            return f"{weight_grams} г"