"""
TOP-EX API integration for shipping cost calculations.
"""
import aiohttp
import asyncio
import logging
import urllib.parse
from typing import Dict, Optional, Any
from config import Config

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
        """Find city code by name using the address book."""
        try:
            await self._ensure_session()
            
            # Search in address book for recipients first
            search_url = f"{self.base_url}/addressBook/list"
            params = {
                'authToken': self.auth_token,
                'type': 'express',
                'attributes[city]': city_name
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') and data.get('items'):
                        # Return the first matching city code
                        return data['items'][0].get('city')
                        
            # If no results, try searching by partial name match
            params['attributes[name]'] = city_name
            del params['attributes[city]']
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') and data.get('items'):
                        # Return the first matching city code
                        return data['items'][0].get('city')
                        
        except Exception as e:
            logger.error(f"Error finding city code for {city_name}: {e}")
            
        return None
        
    async def _get_shipping_costs(self, origin_code: str, destination_code: str, weight: int) -> Dict[str, str]:
        """Get shipping costs from different companies."""
        # This is a placeholder implementation
        # In a real implementation, you would call the actual TOP-EX calculation API
        
        # Since the provided API documentation doesn't include shipping calculation endpoints,
        # we'll return a placeholder response indicating the available information
        
        costs = {
            "TOP-EX": f"Требуется запрос к API расчета (коды городов: {origin_code[:8]}...{destination_code[:8]})",
            "Статус": f"Вес: {weight}г, найдены коды городов",
            "Примечание": "Для расчета стоимости требуется доступ к API расчета стоимости"
        }
        
        return costs
        
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
