"""
TOP-EX API integration for shipping cost calculations.
"""
import aiohttp
import asyncio
import logging
import urllib.parse
import time
from typing import Dict, Optional, Any
from config import Config
from cities_database import find_city_code, get_city_name_by_code

logger = logging.getLogger(__name__)

class TopExAPI:
    """TOP-EX API client for shipping calculations."""
    
    def __init__(self, config: Config):
        """Initialize API client."""
        self.config = config
        self.base_url = config.topex_api_base
        self.auth_token = None
        self.token_expires_at = None
        self.session = None
        self.token_buffer = 300  # Обновляем токен за 5 минут до истечения
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
            )
            
    async def _authenticate(self) -> bool:
        """Authenticate with TOP-EX API and get auth token."""
        try:
            await self._ensure_session()
            
            auth_url = f"{self.base_url}/auth"
            params = {
                'email': self.config.topex_email,
                'password': self.config.topex_password
            }
            
            logger.info("Authenticating with TOP-EX API...")
            
            async with self.session.get(auth_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status'):
                        self.auth_token = data.get('authToken')
                        expire_seconds = data.get('expire', 3600)
                        self.token_expires_at = time.time() + expire_seconds
                        
                        # URL encode the token for safe transmission
                        self.auth_token = urllib.parse.quote(self.auth_token, safe='')
                        
                        logger.info(f"Successfully authenticated with TOP-EX API, token expires in {expire_seconds} seconds")
                        return True
                    else:
                        logger.error(f"Authentication failed: {data.get('error', 'Unknown error')}")
                        return False
                else:
                    logger.error(f"Authentication request failed with status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
            
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid auth token."""
        current_time = time.time()
        
        # Проверяем, есть ли токен и не истек ли он
        if (self.auth_token is None or 
            self.token_expires_at is None or 
            current_time >= (self.token_expires_at - self.token_buffer)):
            
            logger.info("Token is missing or about to expire, refreshing...")
            return await self._authenticate()
        
        # Токен еще действителен
        remaining_time = self.token_expires_at - current_time
        logger.debug(f"Token is valid for {remaining_time:.0f} more seconds")
        return True
        
    async def calculate_shipping_cost(self, origin: str, destination: str, weight: int) -> Dict[str, str]:
        """
        Calculate shipping cost for a route.
        
        Args:
            origin: Origin city name
            destination: Destination city name
            weight: Weight in grams
            
        Returns:
            Dictionary with shipping costs from different companies
        """
        try:
            if not await self._ensure_authenticated():
                return {
                    "Статус": "❌ Ошибка аутентификации",
                    "Сообщение": "Не удалось авторизоваться в TOP-EX API"
                }
                
            # Найдем коды городов в локальной базе данных
            origin_code = await self._find_city_code(origin)
            destination_code = await self._find_city_code(destination)
            
            if not origin_code or not destination_code:
                missing_cities = []
                if not origin_code:
                    missing_cities.append(f"отправления: {origin}")
                if not destination_code:
                    missing_cities.append(f"назначения: {destination}")
                
                return {
                    "Статус": "❌ Города не найдены",
                    "Сообщение": f"Не найдены коды городов {', '.join(missing_cities)}",
                    "Рекомендация": "Проверьте правильность названий городов"
                }
                
            # Попробуем получить стоимость доставки
            costs = await self._get_shipping_costs(origin_code, destination_code, weight)
            
            # Если API endpoint не найден, возвращаем полезную информацию
            if costs.get('status') == 'endpoint_not_found':
                origin_name = get_city_name_by_code(origin_code) or origin
                destination_name = get_city_name_by_code(destination_code) or destination
                
                return {
                    "Маршрут": f"{origin_name} → {destination_name}",
                    "Вес": f"{weight} г",
                    "Статус": "✅ Коды городов найдены в базе данных",
                    "Отправление": f"{origin_name} ({origin_code[:8]}...)",
                    "Назначение": f"{destination_name} ({destination_code[:8]}...)",
                    "Примечание": "⚠️ Для получения точной стоимости требуется настройка API расчета"
                }
            
            return costs
            
        except Exception as e:
            logger.error(f"Error calculating shipping cost: {e}")
            return {
                "Статус": "❌ Ошибка расчета",
                "Сообщение": str(e)
            }
            
    async def _find_city_code(self, city_name: str) -> Optional[str]:
        """Find city code by name using local database."""
        try:
            # Используем локальную базу кодов городов
            city_code = find_city_code(city_name)
            
            if city_code:
                logger.info(f"Found city code for {city_name}: {city_code}")
                return city_code
            else:
                logger.warning(f"City code not found for: {city_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding city code for {city_name}: {e}")
            return None
        
    async def _get_shipping_costs(self, origin_code: str, destination_code: str, weight: int) -> Dict[str, str]:
        """Get shipping costs from different companies using the correct TOP-EX API endpoint."""
        try:
            await self._ensure_session()
            
            logger.info(f"Calculating shipping cost: {origin_code} -> {destination_code}, weight: {weight}g")
            
            # Используем правильный endpoint для расчета стоимости
            calc_url = f"{self.base_url}/cse/calc"
            
            # Параметры согласно документации
            params = {
                'authToken': self.auth_token,
                'attributes[user_id]': '14',  # Значение из документации
                'attributes[sender_city]': origin_code,
                'attributes[recipient_city]': destination_code,
                'attributes[cargo_type]': '4aab1fc6-fc2b-473a-8728-58bcd4ff79ba',  # Для груза
                'attributes[cargo_seats_number]': '1',  # По умолчанию 1 место
                'attributes[cargo_weight]': str(weight)  # Вес в граммах
            }
            
            logger.info(f"Запрос к API: {calc_url}")
            logger.debug(f"Параметры: {params}")
            
            async with self.session.get(calc_url, params=params, timeout=30) as response:
                logger.info(f"Ответ API: статус {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Данные получены: {data}")
                    
                    if data.get('status'):
                        logger.info("✅ Успешно получены данные о стоимости доставки")
                        return self._format_costs_response(data)
                    else:
                        error_msg = data.get('error', 'Неизвестная ошибка API')
                        logger.error(f"❌ Ошибка API: {error_msg}")
                        return {
                            "status": "api_error",
                            "message": f"Ошибка API: {error_msg}"
                        }
                else:
                    text = await response.text()
                    logger.error(f"❌ HTTP ошибка {response.status}: {text[:200]}")
                    return {
                        "status": "http_error",
                        "message": f"HTTP ошибка {response.status}: {text[:100]}"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе стоимости: {e}")
            return {
                "status": "error", 
                "message": f"Ошибка запроса: {str(e)}"
            }
            
    def _format_costs_response(self, data: Dict) -> Dict[str, str]:
        """Format the API response into a readable format."""
        try:
            logger.info(f"Форматирую ответ API: {data}")
            
            formatted = {}
            
            # Проверяем различные форматы ответа от TOP-EX API
            if 'items' in data and data['items']:
                # Обрабатываем массив элементов с расценками
                items = data['items']
                logger.info(f"Найдено {len(items)} элементов с расценками")
                
                for i, item in enumerate(items):
                    # Получаем информацию о компании
                    company_name = item.get('deliveryCompanyLabel', item.get('company_name', f'Компания {i+1}'))
                    
                    # Получаем стоимость
                    cost = item.get('user_price', item.get('retailPrice', item.get('cost', item.get('price', 'Не указано'))))
                    if isinstance(cost, (int, float)):
                        cost_str = f"{cost:.2f} руб."
                    else:
                        cost_str = str(cost)
                    
                    # Получаем метод доставки
                    delivery_method = item.get('deliveryMethodLabel', item.get('tariffName', ''))
                    
                    # Получаем время доставки
                    delivery_time = item.get('totalDeliveryDaysCount', item.get('minPeriod', ''))
                    if delivery_time:
                        time_str = f" ({delivery_time} дн.)"
                    else:
                        time_str = ""
                    
                    # Формируем название с учетом метода доставки
                    if delivery_method:
                        full_name = f"{company_name} - {delivery_method}{time_str}"
                    else:
                        full_name = f"{company_name}{time_str}"
                    
                    formatted[full_name] = cost_str
                
                return formatted
                
            elif 'cost' in data:
                # Единичная стоимость
                cost = data['cost']
                company = data.get('company', 'TOP-EX')
                formatted[company] = f"{cost} руб."
                return formatted
                
            elif 'companies' in data:
                # Массив компаний
                companies = data['companies']
                for company in companies:
                    name = company.get('name', 'Неизвестно')
                    price = company.get('price', company.get('cost', 'Не указано'))
                    formatted[name] = f"{price} руб."
                return formatted
                
            else:
                # Неизвестный формат - покажем как есть
                logger.warning(f"Неизвестный формат ответа: {data}")
                return {
                    "Статус": "✅ Ответ получен",
                    "Данные": str(data)[:500]  # Ограничиваем длину
                }
                
        except Exception as e:
            logger.error(f"Error formatting costs response: {e}")
            return {
                "Статус": "❌ Ошибка форматирования ответа",
                "Ошибка": str(e)
            }
        
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
