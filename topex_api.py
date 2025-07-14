"""
TOP-EX API integration for shipping cost calculations.
"""
import aiohttp
import asyncio
import logging
import urllib.parse
from typing import Dict, Optional, Any
from config import Config
from cities_database import find_city_code

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
                        self.token_expires_at = data.get('expire', 3600)
                        
                        # URL encode the token for safe transmission
                        self.auth_token = urllib.parse.quote(self.auth_token, safe='')
                        
                        logger.info("Successfully authenticated with TOP-EX API")
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
        if not self.auth_token:
            return await self._authenticate()
            
        # For simplicity, we'll re-authenticate for each calculation
        # In production, you might want to implement token refresh logic
        return await self._authenticate()
        
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
                raise Exception("Не удалось авторизоваться в TOP-EX API")
                
            # For this implementation, we'll use the address book to search for cities
            # and then calculate costs. In a real implementation, you might need
            # to use specific calculation endpoints.
            
            # First, try to find city codes
            origin_code = await self._find_city_code(origin)
            destination_code = await self._find_city_code(destination)
            
            if not origin_code or not destination_code:
                # If we can't find city codes, return a message
                return {
                    "Статус": f"Не найдены коды городов: {origin} -> {destination}"
                }
                
            # For demonstration, we'll return placeholder costs
            # In a real implementation, you would call the actual calculation API
            costs = await self._get_shipping_costs(origin_code, destination_code, weight)
            
            return costs
            
        except Exception as e:
            logger.error(f"Error calculating shipping cost: {e}")
            raise
            
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
        """Get shipping costs from different companies."""
        try:
            await self._ensure_session()
            
            # Попробуем найти endpoint для расчета стоимости доставки
            # Обычно это может быть /express/calculate или /shipping/calculate
            calculation_endpoints = [
                "/express/calculateDelivery",
                "/express/calculate", 
                "/shipping/calculate",
                "/delivery/calculate",
                "/calculate"
            ]
            
            for endpoint in calculation_endpoints:
                try:
                    calc_url = f"{self.base_url}{endpoint}"
                    params = {
                        'authToken': self.auth_token,
                        'origin': origin_code,
                        'destination': destination_code,
                        'weight': weight
                    }
                    
                    async with self.session.get(calc_url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status'):
                                logger.info(f"Successfully calculated costs using {endpoint}")
                                return self._format_costs_response(data)
                        elif response.status == 404:
                            # Endpoint не найден, пробуем следующий
                            continue
                        else:
                            logger.warning(f"API endpoint {endpoint} returned status {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for endpoint {endpoint}")
                    continue
                except Exception as e:
                    logger.warning(f"Error with endpoint {endpoint}: {e}")
                    continue
            
            # Если все endpoint'ы не работают, возвращаем информацию о том, что коды найдены
            return {
                "Статус": "Коды городов найдены успешно",
                "Отправление": f"Код: {origin_code[:8]}...",
                "Назначение": f"Код: {destination_code[:8]}...",
                "Вес": f"{weight}г",
                "Примечание": "Для получения стоимости требуется доступ к API расчета"
            }
            
        except Exception as e:
            logger.error(f"Error calculating shipping costs: {e}")
            return {
                "Статус": "Ошибка при расчете стоимости",
                "Ошибка": str(e)
            }
            
    def _format_costs_response(self, data: Dict) -> Dict[str, str]:
        """Format the API response into a readable format."""
        try:
            # Обработаем различные возможные форматы ответа
            if 'costs' in data:
                costs = data['costs']
                formatted = {}
                for company, cost in costs.items():
                    formatted[f"{company}"] = f"{cost} руб."
                return formatted
            elif 'companies' in data:
                companies = data['companies']
                formatted = {}
                for company in companies:
                    name = company.get('name', 'Неизвестно')
                    price = company.get('price', 'Не указано')
                    formatted[name] = f"{price} руб."
                return formatted
            else:
                return {
                    "Статус": "Ответ получен",
                    "Данные": str(data)
                }
        except Exception as e:
            logger.error(f"Error formatting costs response: {e}")
            return {
                "Статус": "Ошибка форматирования ответа",
                "Ошибка": str(e)
            }
        
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
