# Telegram Bot for Shipping Cost Calculator

## Overview

This is a Telegram bot application that processes Excel files containing shipping route data and calculates delivery costs using the TOP-EX API. Users can upload Excel files with shipping information (origin city, destination city, weight) and receive cost estimates from different shipping companies.

## User Preferences

Preferred communication style: Simple, everyday language.
Code requirements: All code must have detailed Russian comments and follow SOLID/DRY principles.
Documentation: README.md must contain comprehensive description of all modules, variables, and functions.

## System Architecture

### Core Architecture
- **Language**: Python 3.x
- **Framework**: python-telegram-bot library for Telegram Bot API integration
- **File Processing**: pandas for Excel file handling
- **HTTP Client**: aiohttp for asynchronous API calls
- **Logging**: Python's built-in logging module

### Application Structure
The application follows a modular architecture with clear separation of concerns:

1. **Bot Handler Layer** (`bot.py`) - Manages Telegram interactions
2. **API Integration Layer** (`topex_api.py`) - Handles external API communication
3. **Data Processing Layer** (`excel_processor.py`) - Processes Excel files
4. **Configuration Layer** (`config.py`) - Manages environment variables and settings
5. **Utility Layer** (`utils.py`) - Common validation and formatting functions

## Key Components

### TelegramBot Class
- Handles user interactions through Telegram
- Processes file uploads and text messages
- Manages bot commands (/start, /help)
- Coordinates between Excel processing and API calls

### ExcelProcessor Class
- Extracts shipping route data from Excel files
- Supports multiple column naming patterns (multi-language)
- Validates data integrity and format
- Handles both .xlsx and .xls file formats

### TopExAPI Class
- Manages authentication with TOP-EX shipping API
- Handles rate limiting and request timeouts
- Provides shipping cost calculations
- Implements token management and session handling

### Configuration Management
- Environment variable-based configuration
- Required variables: TELEGRAM_BOT_TOKEN, TOPEX_EMAIL, TOPEX_PASSWORD
- Configurable API settings (timeouts, file size limits, rate limits)

## Data Flow

1. **User Input**: User uploads Excel file via Telegram
2. **File Processing**: Excel file is processed to extract shipping routes
3. **Data Validation**: Route data is validated for completeness and format
4. **API Authentication**: Bot authenticates with TOP-EX API
5. **Cost Calculation**: Shipping costs are calculated for each route
6. **Response Generation**: Results are formatted and sent back to user

### Data Structure
The system expects Excel files with columns containing:
- Origin city (откуда/from/origin)
- Destination city (куда/to/destination)  
- Weight (вес/weight) in grams

## External Dependencies

### APIs
- **Telegram Bot API**: Primary interface for user interactions
- **TOP-EX API**: External shipping cost calculation service

### Python Libraries
- `python-telegram-bot`: Telegram bot framework
- `pandas`: Excel file processing
- `aiohttp`: Asynchronous HTTP client
- `asyncio`: Asynchronous programming support

### File Handling
- Supports Excel formats (.xlsx, .xls)
- Maximum file size: 10MB
- Temporary file processing for uploaded documents

## Deployment Strategy

### Environment Setup
The application requires environment variables for:
- Telegram bot token
- TOP-EX API credentials
- Optional configuration overrides

### Runtime Requirements
- Python 3.x environment
- Async/await support
- File system access for temporary file processing
- Network access for API calls

### Error Handling
- Comprehensive logging to both file and console
- Graceful error handling for API failures
- User-friendly error messages in Russian
- Validation of all inputs and configurations

### Performance Considerations
- Rate limiting for API calls (1 second delay between requests)
- Request timeouts (30 seconds default)
- Session management for HTTP connections
- Memory-efficient file processing

The architecture is designed to be scalable and maintainable, with clear separation between bot logic, data processing, and external integrations.

## Recent Changes: Latest modifications with dates

### July 14, 2025 - Initial Implementation Complete
- ✅ Telegram bot successfully implemented and running
- ✅ Excel file processing working for Russian column names
- ✅ TOP-EX API integration with authentication
- ✅ Complete workflow from file upload to cost calculation
- ✅ Environment variables configuration system
- ✅ Comprehensive error handling and logging
- ✅ Multi-language support (Russian/English columns)
- ✅ Rate limiting and request timeout management

### August 14, 2025 - Major Architecture Overhaul
- ✅ **BREAKING CHANGE**: Redesigned input format - Excel files now require only "Откуда" and "Куда" columns (no weight column)
- ✅ **NEW FEATURE**: Multi-weight category testing - bot now tests 5 weight categories: 0.5kg, 1kg, 2kg, 5kg, 10kg
- ✅ **NEW FEATURE**: Excel output generation - results are now returned as Excel files instead of text messages
- ✅ **NEW MODULE**: ExcelGenerator class for creating formatted result files
- ✅ **ENHANCED**: Cheapest offer detection algorithm for each weight category
- ✅ **UPDATED**: Bot messages and help text to reflect new workflow
- ✅ **IMPROVED**: Result data structure with weight-based categorization

### August 14, 2025 - Critical Bug Fixes and Application Recovery
- 🛠️ **RESOLVED**: python-telegram-bot package corruption - manually reconstructed missing telegram/__init__.py file
- 🛠️ **RESOLVED**: Conflicting telegram stub package (v0.0.1) was interfering with python-telegram-bot installation
- 🛠️ **RESOLVED**: ExcelProcessor type errors in pandas DataFrame index operations
- 🛠️ **RESOLVED**: Missing class imports causing ImportError exceptions
- 🛠️ **RESOLVED**: isinstance() type checking errors by replacing None assignments with proper stub classes
- 🛠️ **TECHNICAL FIX**: Systematically added all required Telegram Bot API class imports (60+ classes)
- 🛠️ **TECHNICAL FIX**: Fixed import chains for games, inline, files, and core telegram modules

### August 15, 2025 - Complete Architecture Redesign with SOLID Principles
- ✅ **ARCHITECTURE OVERHAUL**: Полная реструктуризация согласно принципам SOLID и DRY
- ✅ **CLEAN ARCHITECTURE**: Внедрена чистая архитектура с разделением на слои
- ✅ **DEPENDENCY INJECTION**: Создан ApplicationContainer для управления зависимостями
- ✅ **INTERFACES**: Все компоненты работают через абстрактные интерфейсы
- ✅ **MODULAR DESIGN**: Четкое разделение на interfaces, implementations, models, services
- ✅ **COMPREHENSIVE DOCS**: Создан детальный README.md с описанием всех модулей
- ✅ **RUSSIAN COMMENTS**: Все новые компоненты снабжены подробными комментариями на русском языке
- ✅ **TELEGRAM IMPORTS**: Восстановлены все необходимые импорты telegram библиотеки
- ✅ **TESTING**: Базовые компоненты протестированы и работают корректно

### Current Status
- ✅ **NEW ARCHITECTURE**: Новая модульная архитектура полностью готова
- ✅ **SOLID PRINCIPLES**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- ✅ **DRY IMPLEMENTATION**: Устранение дублирования кода через централизованную конфигурацию
- ✅ **LEGACY COMPATIBILITY**: Старая версия сохранена для обратной совместимости
- **NEW ENTRY POINT**: src/main.py - новая точка входа с DI контейнером
- **CONFIGURATION**: Полностью настраиваемая система через переменные окружения
- **DOCUMENTATION**: Исчерпывающая документация всех модулей, функций и переменных
- **TESTING**: Система тестирования архитектуры и компонентов

### Новая структура проекта:
```
src/
├── interfaces/          # Абстракции (Принцип DIP)
├── implementations/     # Конкретные реализации
├── models/             # Модели данных
├── services/           # Бизнес-логика
└── main.py            # Точка входа с DI контейнером
```

### Основные преимущества новой архитектуры:
- **Тестируемость**: Каждый компонент может тестироваться независимо
- **Расширяемость**: Легко добавлять новые API провайдеры, форматы файлов
- **Поддерживаемость**: Четкое разделение ответственности
- **Конфигурируемость**: Все настройки через переменные окружения
- **Документированность**: Подробные комментарии и README.md

Система готова к production использованию и дальнейшему развитию