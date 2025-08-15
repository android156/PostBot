#!/usr/bin/env python3
"""
Скрипт для исправления единиц измерения веса с граммов на килограммы.
"""
import os
import re

def fix_weight_units():
    """Исправляет единицы измерения веса в проекте."""
    
    # Файлы для исправления
    files_to_fix = [
        'src/models/shipping_calculation.py',
        'src/implementations/topex_api_client.py',
        'src/services/bot_service.py'
    ]
    
    replacements = [
        # Комментарии и документация
        (r'в граммах', 'в килограммах'),
        (r'граммах', 'килограммах'),
        (r'weight.*graммах', 'weight в килограммах'),
        (r'Вес в граммах', 'Вес в килограммах'),
        
        # Конвертация веса
        (r'self\.weight / 1000\.0', 'float(self.weight)'),
        (r'weight / 1000', 'weight'),
        
        # Единицы в логах
        (r'(\d+)г', r'\1кг'),
        (r'{weight}г', '{weight}кг'),
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Исправляю {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Применяем замены
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"  ✓ {file_path} исправлен")
    
    print("✅ Все единицы измерения исправлены на килограммы")

if __name__ == "__main__":
    fix_weight_units()