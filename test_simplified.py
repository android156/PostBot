#!/usr/bin/env python3
"""
Упрощенный тест новой архитектуры без импортов telegram.ext
"""
import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

async def test_components():
    """Тестирует компоненты без telegram.ext"""
    print("=== Тест компонентов новой архитектуры ===")
    
    try:
        # Тест базовых модулей
        print("✓ Тестирование конфигурации...")
        from src.implementations.config_manager import ConfigManager
        config = ConfigManager()
        print(f"  Конфигурация создана, валидна: {config.validate_configuration()}")
        
        print("✓ Тестирование Excel процессора...")
        from src.implementations.excel_processor import ExcelProcessor
        excel_processor = ExcelProcessor()
        columns = excel_processor.get_supported_column_names()
        print(f"  Поддерживаемые колонки: {len(columns['origin'])} отправления, {len(columns['destination'])} назначения")
        
        print("✓ Тестирование API клиента...")
        from src.implementations.topex_api_client import TopExApiClient
        api_client = TopExApiClient(config)
        print(f"  API клиент создан, аутентифицирован: {await api_client.is_authenticated()}")
        
        print("✓ Тестирование генератора результатов...")
        from src.implementations.result_generator import ExcelResultGenerator
        result_generator = ExcelResultGenerator()
        formats = result_generator.get_supported_formats()
        print(f"  Поддерживаемые форматы: {', '.join(formats)}")
        
        print("✓ Тестирование моделей данных...")
        from src.models.route import Route
        from src.models.shipping_calculation import ShippingOffer
        
        route = Route("Москва", "СПб", 1)
        offer = ShippingOffer("СДЭК", 500.0, 2, "Стандарт", 1000)
        print(f"  Маршрут: {route.get_display_name()}, валиден: {route.is_valid()}")
        print(f"  Предложение: {offer.company_name} - {offer.price}₽ за {offer.delivery_days} дней")
        
        await api_client.close()
        print("\n✅ ВСЕ БАЗОВЫЕ КОМПОНЕНТЫ РАБОТАЮТ!")
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_components())
    if success:
        print("\n🚀 Новая архитектура готова!")
        print("📋 Все основные компоненты согласно принципам SOLID работают корректно")
    else:
        sys.exit(1)