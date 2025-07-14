"""
Telegram bot implementation for processing Excel files with shipping routes.
"""
import logging
import asyncio
import os
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
        self.application = Application.builder().token(config.telegram_token).build()
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

Этот бот поможет вам рассчитать стоимость доставки посылок через различные компании.

**Как использовать:**
1. Отправьте Excel файл с маршрутами доставки
2. Файл должен содержать колонки: город отправления, город получения, вес
3. Бот обработает файл и вернет стоимость доставки от разных компаний

**Поддерживаемые форматы:** .xlsx, .xls

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
• Вес посылки (в граммах или килограммах)

**Примеры названий колонок:**
• "Откуда", "Куда", "Вес"
• "Отправитель", "Получатель", "Масса"
• "From", "To", "Weight"

**Требования к файлу:**
• Максимальный размер: 10MB
• Форматы: .xlsx, .xls
• Первая строка должна содержать заголовки

**Поддержка:**
Если у вас возникли проблемы, проверьте:
1. Правильность формата файла
2. Наличие обязательных колонок
3. Корректность данных о городах и весе
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
            "📄 Пожалуйста, отправьте Excel файл с данными о доставке.\n"
            "Используйте /help для получения информации о формате файла."
        )
        
    async def get_shipping_costs(self, shipping_data):
        """Get shipping costs for all routes."""
        results = []
        
        for i, route in enumerate(shipping_data, 1):
            try:
                # Add delay between requests to respect rate limits
                if i > 1:
                    await asyncio.sleep(self.config.rate_limit_delay)
                    
                # Get costs for this route
                costs = await self.topex_api.calculate_shipping_cost(
                    origin=route['origin'],
                    destination=route['destination'],
                    weight=route['weight']
                )
                
                results.append({
                    'route_number': i,
                    'origin': route['origin'],
                    'destination': route['destination'],
                    'weight': route['weight'],
                    'costs': costs,
                    'error': None
                })
                
            except Exception as e:
                logger.error(f"Error calculating cost for route {i}: {e}")
                results.append({
                    'route_number': i,
                    'origin': route['origin'],
                    'destination': route['destination'],
                    'weight': route['weight'],
                    'costs': None,
                    'error': str(e)
                })
                
        return results
        
    async def send_results(self, update: Update, results):
        """Send formatted results to user."""
        if not results:
            await update.message.reply_text("❌ Нет данных для отображения")
            return
            
        # Create summary message
        total_routes = len(results)
        successful_routes = len([r for r in results if r['error'] is None])
        
        summary = f"""📊 Результаты расчета стоимости доставки

📈 Обработано маршрутов: {total_routes}
✅ Успешно: {successful_routes}
❌ Ошибок: {total_routes - successful_routes}

---"""
        
        # Send summary first
        await update.message.reply_text(summary)
        
        # Format and send results for each route
        for result in results:
            try:
                route_text = f"""🚚 Маршрут {result['route_number']}
📍 Откуда: {result['origin']}
📍 Куда: {result['destination']}
⚖️ Вес: {result['weight']} г

"""
                
                if result['error']:
                    route_text += f"❌ Ошибка: {result['error']}"
                elif result['costs']:
                    route_text += "💰 Стоимость доставки:\n"
                    for company, cost in result['costs'].items():
                        # Clean text to avoid Telegram parsing issues
                        company_clean = str(company).replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
                        cost_clean = str(cost).replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
                        route_text += f"• {company_clean}: {cost_clean}\n"
                else:
                    route_text += "❌ Не удалось получить стоимость"
                
                route_text += "\n---\n"
                
                # Send each route as a separate message to avoid length limits
                await update.message.reply_text(route_text)
                
            except Exception as e:
                logger.error(f"Error sending route result: {e}")
                # Send simple error message
                error_text = f"❌ Ошибка отправки результата для маршрута {result['route_number']}: {result['origin']} → {result['destination']}"
                await update.message.reply_text(error_text)
            

