#!/usr/bin/env python3
"""
Тестирование новой архитектуры бота.

Этот скрипт проверяет работоспособность всех компонентов новой архитектуры
без запуска реального Telegram бота.
"""
import sys
import asyncio
import logging
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

async def test_architecture():
    """
    Тестирует все компоненты новой архитектуры.
    """
    print("=" * 60)
    print("Тестирование новой архитектуры Telegram бота")
    print("=" * 60)
    
    try:
        # Тест 1: Импорт всех модулей
        print("✓ Тест 1: Проверка импортов...")
        from src.main import ApplicationContainer
        print("  ✓ ApplicationContainer импортирован")
        
        # Тест 2: Создание контейнера зависимостей
        print("✓ Тест 2: Создание контейнера зависимостей...")
        container = ApplicationContainer()
        print("  ✓ Контейнер создан успешно")
        
        # Тест 3: Проверка конфигурации
        print("✓ Тест 3: Проверка конфигурации...")
        config = container.get_config()
        config_dict = config.to_dict()
        print(f"  ✓ Конфигурация загружена: {len(config_dict)} параметров")
        print(f"  ✓ Telegram token: {'установлен' if config_dict['telegram_token_set'] else 'НЕ УСТАНОВЛЕН'}")
        print(f"  ✓ API credentials: {'установлены' if config_dict['api_credentials']['email_set'] else 'НЕ УСТАНОВЛЕНЫ'}")
        
        # Тест 4: Проверка сервиса бота
        print("✓ Тест 4: Проверка сервиса бота...")
        bot_service = container.get_bot_service()
        print("  ✓ BotService создан успешно")
        
        # Тест 5: Проверка Excel процессора
        print("✓ Тест 5: Проверка Excel процессора...")
        excel_processor = container._components['excel_processor']
        supported_columns = excel_processor.get_supported_column_names()
        print(f"  ✓ Поддержка колонок отправления: {len(supported_columns['origin'])}")
        print(f"  ✓ Поддержка колонок назначения: {len(supported_columns['destination'])}")
        
        # Тест 6: Проверка генератора результатов
        print("✓ Тест 6: Проверка генератора результатов...")
        result_generator = container._components['result_generator']
        supported_formats = result_generator.get_supported_formats()
        print(f"  ✓ Поддерживаемые форматы: {', '.join(supported_formats)}")
        
        # Тест 7: Проверка весовых категорий
        print("✓ Тест 7: Проверка весовых категорий...")
        weight_categories = config.get_weight_categories()
        weight_kg = [f"{w/1000:.1f}кг" for w in weight_categories]
        print(f"  ✓ Весовые категории: {', '.join(weight_kg)}")
        
        # Тест 8: Проверка логирования
        print("✓ Тест 8: Проверка системы логирования...")
        log_settings = config.get_logging_settings()
        print(f"  ✓ Уровень логирования: {log_settings['level']}")
        print(f"  ✓ Файл логов: {log_settings['file_path']}")
        
        # Тест 9: Проверка моделей данных
        print("✓ Тест 9: Проверка моделей данных...")
        from src.models.route import Route
        from src.models.shipping_calculation import ShippingOffer, WeightCategoryResult
        
        # Создаем тестовый маршрут
        test_route = Route(origin="Москва", destination="Санкт-Петербург", row_index=1)
        print(f"  ✓ Тестовый маршрут: {test_route.get_display_name()}")
        print(f"  ✓ Валидность маршрута: {test_route.is_valid()}")
        
        # Создаем тестовое предложение
        test_offer = ShippingOffer(
            company_name="Тестовая компания",
            price=500.0,
            delivery_days=3,
            tariff_name="Стандарт",
            weight=1000
        )
        print(f"  ✓ Тестовое предложение: {test_offer.company_name} - {test_offer.price}₽")
        print(f"  ✓ Цена за кг: {test_offer.get_price_per_kg():.2f}₽")
        
        # Тест 10: Проверка API клиента
        print("✓ Тест 10: Проверка API клиента...")
        api_client = container._components['api_client']
        is_authenticated = await api_client.is_authenticated()
        print(f"  ✓ Статус аутентификации: {'аутентифицирован' if is_authenticated else 'не аутентифицирован'}")
        
        # Тест 11: Финальная очистка
        print("✓ Тест 11: Очистка ресурсов...")
        await container.cleanup()
        print("  ✓ Ресурсы освобождены")
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🚀 Новая архитектура готова к работе")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """
    Главная функция тестирования.
    """
    # Настраиваем базовое логирование для тестов
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = await test_architecture()
    
    if success:
        print("\n📋 РЕКОМЕНДАЦИИ:")
        print("1. Установите переменные окружения для полной функциональности:")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - TOPEX_EMAIL") 
        print("   - TOPEX_PASSWORD")
        print("2. Запустите основное приложение: python src/main.py")
        print("3. Обратитесь к README.md для подробной документации")
    else:
        print("\n❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО")
        print("Проверьте ошибки выше и исправьте проблемы")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())