"""
Telegram bot implementation for processing Excel files with shipping routes.
"""
import logging
import asyncio
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from excel_processor import ExcelProcessor
from topex_api import TopExAPI
from config import Config
import tempfile

logger = logging.getLogger(__name__)

class TelegramBot:
    """Main Telegram bot class."""
    
    def __init__(self, config: Config):
        """Initialize the bot with configuration."""
        self.config = config
        self.application = Application.builder().token(config.telegram_token or "").build()
        self.excel_processor = ExcelProcessor()
        self.topex_api = TopExAPI(config)
        
        # Setup handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup bot command and message handlers."""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🚚 **Добро пожаловать в бот расчета стоимости доставки!**

Этот бот поможет вам найти самые дешевые варианты доставки для разных весовых категорий.

**Как использовать:**
1. Отправьте Excel файл с маршрутами доставки
2. Файл должен содержать колонки: "Откуда", "Куда" (без веса)
3. Бот протестирует несколько весовых категорий и вернет Excel файл с самыми дешевыми предложениями

**Весовые категории:** 0.5кг, 1кг, 2кг, 5кг, 10кг

Для получения справки используйте команду /help
        """
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
📋 **Справка по использованию бота**

**Формат Excel файла:**
Файл должен содержать следующие колонки:
• Город отправления (или код КЛАДР)
• Город получения (или код КЛАДР)

**Примеры названий колонок:**
• "Откуда", "Куда"
• "Отправитель", "Получатель"
• "From", "To"

**Как работает бот:**
1. Для каждого маршрута тестируются весовые категории: 0.5кг, 1кг, 2кг, 5кг, 10кг
2. Находится самое дешевое предложение в каждой категории
3. Результаты сохраняются в Excel файл с информацией о компании, цене и сроках

**Требования к файлу:**
• Максимальный размер: 10MB
• Форматы: .xlsx, .xls
• Первая строка должна содержать заголовки
        """
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
        
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads."""
        document = update.message.document
        
        # Check file size
        if document.file_size > self.config.max_file_size:
            await update.message.reply_text(
                f"❌ Файл слишком большой. Максимальный размер: {self.config.max_file_size // (1024*1024)}MB"
            )
            return
            
        # Check file extension
        if not document.file_name.lower().endswith(('.xlsx', '.xls')):
            await update.message.reply_text(
                "❌ Поддерживаются только Excel файлы (.xlsx, .xls)"
            )
            return
            
        # Send processing message
        processing_msg = await update.message.reply_text("📊 Обрабатываю файл...")
        
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
                await file.download_to_drive(tmp_file.name)
                temp_file_path = tmp_file.name
                
            try:
                # Process Excel file
                await processing_msg.edit_text("📋 Читаю данные из файла...")
                shipping_data = self.excel_processor.process_file(temp_file_path)
                
                if not shipping_data:
                    await processing_msg.edit_text("❌ Не удалось найти данные о доставке в файле")
                    return
                    
                # Get shipping costs
                await processing_msg.edit_text("💰 Получаю стоимость доставки...")
                results = await self.get_shipping_costs(shipping_data)
                
                # Format and send results
                await processing_msg.edit_text("📤 Формирую результаты...")
                await self.send_results(update, results)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await processing_msg.edit_text(f"❌ Ошибка обработки файла: {str(e)}")
            
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        await update.message.reply_text(
            "📄 Пожалуйста, отправьте Excel файл с маршрутами доставки (только колонки 'Откуда' и 'Куда').\n"
            "Бот протестирует разные весовые категории и вернет Excel файл с результатами.\n"
            "Используйте /help для получения информации о формате файла."
        )
        
    async def get_shipping_costs(self, shipping_data):
        """Get shipping costs for all routes with multiple weight categories."""
        results = []
        
        for i, route in enumerate(shipping_data, 1):
            try:
                route_result = {
                    'route_number': i,
                    'origin': route['origin'],
                    'destination': route['destination'],
                    'weight_results': {}
                }
                
                # Test each weight category
                for weight in self.config.weight_categories:
                    try:
                        # Add delay between requests to respect rate limits
                        await asyncio.sleep(self.config.rate_limit_delay)
                        
                        logger.info(f"Testing route {i} ({route['origin']} → {route['destination']}) with weight {weight}g")
                        
                        # Get costs for this route and weight
                        costs = await self.topex_api.calculate_shipping_cost(
                            origin=route['origin'],
                            destination=route['destination'],
                            weight=weight
                        )
                        
                        # Find cheapest offer
                        cheapest_offer = self._find_cheapest_offer(costs)
                        
                        route_result['weight_results'][weight] = {
                            'cheapest_offer': cheapest_offer,
                            'all_offers': costs,
                            'error': None
                        }
                        
                    except Exception as e:
                        logger.error(f"Error calculating cost for route {i}, weight {weight}g: {e}")
                        route_result['weight_results'][weight] = {
                            'cheapest_offer': None,
                            'all_offers': None,
                            'error': str(e)
                        }
                
                results.append(route_result)
                
            except Exception as e:
                logger.error(f"Error processing route {i}: {e}")
                results.append({
                    'route_number': i,
                    'origin': route['origin'],
                    'destination': route['destination'],
                    'weight_results': {},
                    'error': str(e)
                })
                
        return results
    
    def _find_cheapest_offer(self, costs):
        """Find the cheapest offer from API response."""
        if not costs or not isinstance(costs, dict):
            return None
            
        cheapest = None
        min_price = float('inf')
        
        for offer_name, offer_details in costs.items():
            try:
                # Extract price from offer details string
                if '|' in str(offer_details):
                    parts = str(offer_details).split('|')
                    price_part = None
                    for part in parts:
                        if 'Цена:' in part:
                            price_part = part
                            break
                    
                    if price_part:
                        # Extract numeric price
                        import re
                        price_match = re.search(r'(\d+\.?\d*)', price_part)
                        if price_match:
                            price = float(price_match.group(1))
                            if price < min_price:
                                min_price = price
                                
                                # Extract company, tariff, delivery days
                                company_parts = offer_name.split(' - ')
                                company = company_parts[0] if company_parts else offer_name
                                tariff = company_parts[1] if len(company_parts) > 1 else ''
                                
                                # Extract delivery days from details
                                delivery_days = ''
                                for part in parts:
                                    if 'Срок:' in part:
                                        delivery_days = part.replace('Срок:', '').strip()
                                        break
                                
                                cheapest = {
                                    'company': company,
                                    'tariff': tariff,
                                    'price': price,
                                    'delivery_days': delivery_days,
                                    'full_offer': offer_name
                                }
            except Exception as e:
                logger.error(f"Error parsing offer {offer_name}: {e}")
                continue
        
        return cheapest
        
    async def send_results(self, update: Update, results):
        """Generate and send Excel file with results."""
        if not results:
            await update.message.reply_text("❌ Нет данных для отображения")
            return
            
        try:
            # Import the Excel generator
            from excel_generator import ExcelGenerator
            
            # Create summary message
            total_routes = len(results)
            successful_routes = len([r for r in results if not r.get('error')])
            
            summary = f"""📊 Формирую Excel файл с результатами...

📈 Обработано маршрутов: {total_routes}
✅ Успешно: {successful_routes}
❌ Ошибок: {total_routes - successful_routes}

Тестировались весовые категории: {', '.join([f'{w/1000:.1f}кг' for w in self.config.weight_categories])}"""
            
            # Send summary first
            status_msg = await update.message.reply_text(summary)
            
            # Generate Excel file
            excel_generator = ExcelGenerator()
            import tempfile
            import os
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            timestamp = int(datetime.now().timestamp())
            output_filename = f"shipping_results_{timestamp}.xlsx"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Generate the Excel file
            excel_generator.generate_results_file(results, output_path)
            
            # Update status
            await status_msg.edit_text("📤 Отправляю Excel файл...")
            
            # Send the Excel file
            with open(output_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=f"Результаты_доставки_{timestamp}.xlsx",
                    caption="📋 Готово! Excel файл с результатами расчета стоимости доставки"
                )
            
            # Clean up temporary file
            if os.path.exists(output_path):
                os.unlink(output_path)
                
        except Exception as e:
            logger.error(f"Error generating Excel results: {e}")
            await update.message.reply_text(f"❌ Ошибка при создании Excel файла: {str(e)}")
            

