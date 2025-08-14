# Telegram Bot for Shipping Cost Calculator

## Overview

This is a Telegram bot application that processes Excel files containing shipping route data and calculates delivery costs using the TOP-EX API. Users can upload Excel files with shipping information (origin city, destination city, weight) and receive cost estimates from different shipping companies.

## User Preferences

Preferred communication style: Simple, everyday language.

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

### Current Status
- Bot is operational with completely new workflow
- **INPUT**: Excel files with routes (only origin/destination, no weight required)
- **PROCESSING**: Each route tested with 5 different weight categories automatically
- **OUTPUT**: Excel file containing cheapest shipping options for each weight category
- **API**: TOP-EX API integration working with `/cse/calc` endpoint
- **FEATURES**: Real-time cost comparison, automatic cheapest offer selection, comprehensive Excel reporting
- System now provides comprehensive shipping cost analysis across multiple weight categories
- Bot successfully processes routes and generates detailed Excel reports with best pricing options