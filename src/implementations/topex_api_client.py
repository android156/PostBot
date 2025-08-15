"""
Реализация клиента TOP-EX API.

Конкретная реализация интерфейса IApiClient для работы 
с API сервиса TOP-EX для расчета стоимости доставки.

Принципы SOLID:
- Single Responsibility Principle (SRP): Отвечает только за API TOP-EX
- Open/Closed Principle (OCP): Легко расширяется для новых методов API
- Dependency Inversion Principle (DIP): Реализует абстракцию IApiClient
"""
import aiohttp
import asyncio
import logging
import urllib.parse
import time
from typing import Dict, Optional, Any, List

from ..interfaces.i_api_client import IApiClient
from ..interfaces.i_config import IConfig
from ..models.shipping_calculation import ShippingOffer

logger = logging.getLogger(__name__)


class TopExApiClient(IApiClient):
    """
    Конкретная реализация клиента TOP-EX API.
    
    Обеспечивает взаимодействие с API TOP-EX для получения
    расчетов стоимости доставки от различных транспортных компаний.
    
    Включает аутентификацию, кэширование токенов и обработку ошибок.
    """

    def __init__(self, config: IConfig):
        """
        Инициализирует клиент TOP-EX API.
        
        Args:
            config (IConfig): Интерфейс конфигурации для получения настроек
        """
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None

        # Настройки аутентификации
        self._auth_token: Optional[str] = None  # URL-кодированный токен для GET параметров
        self._raw_auth_token: Optional[str] = None  # Оригинальный токен для POST запросов
        self._token_expires_at: Optional[float] = None
        self._token_buffer = 300  # Обновляем токен за 5 минут до истечения

        # Кеширование списка городов
        self._cities_cache: Optional[List[Dict[str, str]]] = None
        self._cities_cache_expires_at: Optional[float] = None
        self._cities_cache_ttl = 3600  # Кеш на 1 час

        # Получаем настройки из конфигурации
        api_credentials = self._config.get_api_credentials()
        api_settings = self._config.get_api_settings()

        self._email = api_credentials['email']
        self._password = api_credentials['password']
        self._base_url = api_credentials['base_url']
        self._timeout = api_settings['timeout']
        self._retry_count = api_settings['retry_count']
        self._rate_limit_delay = api_settings['rate_limit_delay']

        logger.info(f"TopExApiClient инициализирован для {self._base_url}")

    async def authenticate(self) -> bool:
        """
        Выполняет аутентификацию в TOP-EX API.
        
        Получает токен авторизации, который используется
        для всех последующих запросов к API.
        
        Returns:
            bool: True если аутентификация успешна
        """
        try:
            await self._ensure_session()

            auth_url = f"{self._base_url}/auth"
            params = {'email': self._email, 'password': self._password}

            logger.info("Выполняю аутентификацию в TOP-EX API...")

            # Выполняем запрос аутентификации
            async with self._session.get(auth_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if data and data.get('status'):
                        # Сохраняем токен и время истечения
                        self._raw_auth_token = data.get('authToken')  # Оригинальный токен для POST запросов
                        expire_seconds = data.get('expire', 3600)
                        self._token_expires_at = time.time() + expire_seconds

                        # URL-кодированный токен только для GET параметров
                        self._auth_token = urllib.parse.quote(self._raw_auth_token,
                                                              safe='')

                        logger.info(
                            f"Аутентификация успешна, токен истекает через {expire_seconds} секунд"
                        )
                        return True
                    else:
                        error_msg = data.get('error', 'Неизвестная ошибка')
                        logger.error(f"Ошибка аутентификации: {error_msg}")
                        return False
                else:
                    logger.error(
                        f"HTTP ошибка при аутентификации: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Исключение при аутентификации: {e}")
            return False

    async def calculate_shipping_cost(self, origin: str, destination: str,
                                      weight: float) -> Dict[str, Any]:
        """
        Рассчитывает стоимость доставки для заданного маршрута.
        
        Args:
            origin (str): Код или название города отправления
            destination (str): Код или название города назначения
            weight (float): Вес груза в килокилограммах
            
        Returns:
            Dict[str, Any]: Результат расчета с предложениями
        """
        try:
            # Проверяем аутентификацию
            if not await self.is_authenticated():
                if not await self.authenticate():
                    return self._create_error_result(
                        "Ошибка аутентификации", "Не удалось войти в систему")

            # Находим коды городов, если переданы названия
            origin_code = await self._resolve_city_code(origin)
            destination_code = await self._resolve_city_code(destination)

            if not origin_code or not destination_code:
                missing_cities = []
                if not origin_code:
                    missing_cities.append(f"отправления: {origin}")
                if not destination_code:
                    missing_cities.append(f"назначения: {destination}")

                return self._create_error_result(
                    "Города не найдены",
                    f"Не найдены коды городов {', '.join(missing_cities)}")

            # Выполняем расчет стоимости
            calculation_result = await self._perform_calculation(
                origin_code, destination_code, weight)

            # Добавляем задержку для соблюдения rate limit
            await asyncio.sleep(self._rate_limit_delay)

            return calculation_result

        except Exception as e:
            logger.error(f"Ошибка расчета стоимости доставки: {e}")
            return self._create_error_result("Ошибка расчета", str(e))

    async def get_available_cities(self) -> List[Dict[str, str]]:
        """
        Получает список доступных городов для доставки.
        
        Returns:
            List[Dict[str, str]]: Список городов с кодами
        """
        try:
            if not await self.is_authenticated():
                if not await self.authenticate():
                    logger.error(
                        "Не удалось получить список городов: нет аутентификации"
                    )
                    return []

            await self._ensure_session()

            cities_url = f"{self._base_url}/cse/cityList"
            
            # Согласно документации API - это POST запрос с токеном в теле
            # Используем оригинальный токен без URL-кодирования
            data = {'authToken': self._raw_auth_token}
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            logger.debug(f"Запрашиваю список городов: POST {cities_url}")

            async with self._session.post(cities_url, 
                                         data=data, 
                                         headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data and response_data.get('status'):
                        cities = response_data.get('data', [])
                        logger.info(f"Получено {len(cities)} городов из API")
                        return cities
                    else:
                        error_msg = response_data.get('error', 'Неизвестная ошибка')
                        logger.error(f"API вернул ошибку: {error_msg}")
                        return []
                else:
                    response_text = await response.text()
                    logger.error(
                        f"HTTP ошибка при получении городов: {response.status}, ответ: {response_text}"
                    )
                    return []

        except Exception as e:
            logger.error(f"Ошибка получения списка городов: {e}")
            return []

    async def is_authenticated(self) -> bool:
        """
        Проверяет наличие действующей аутентификации.
        
        Returns:
            bool: True если есть валидный токен
        """
        if not self._auth_token or not self._raw_auth_token or not self._token_expires_at:
            return False

        current_time = time.time()
        # Проверяем, не истек ли токен (с учетом буфера)
        return current_time < (self._token_expires_at - self._token_buffer)

    async def close(self) -> None:
        """
        Закрывает HTTP сессию и освобождает ресурсы.
        """
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("HTTP сессия TOP-EX API закрыта")

    async def _ensure_session(self) -> None:
        """
        Обеспечивает наличие HTTP сессии.
        
        Приватный метод для ленивого создания aiohttp сессии.
        """
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
            logger.debug("Создана новая HTTP сессия для TOP-EX API")

    async def _resolve_city_code(self, city_input: str) -> Optional[str]:
        """
        Преобразует название города или код в код города.
        
        Если передан код (числовая строка), возвращает его как есть.
        Если передано название, ищет код через API TOP-EX с кешированием.
        
        Args:
            city_input (str): Название или код города
            
        Returns:
            Optional[str]: Код города или None если не найден
        """
        # Проверяем, не является ли входная строка уже кодом
        if city_input.isdigit():
            logger.debug(f"Получен код города: {city_input}")
            return city_input

        # Получаем список городов (с кешированием)
        cities = await self._get_cached_cities()
        if not cities:
            logger.error("Не удалось получить список городов для поиска")
            return None

        # Нормализуем название для поиска
        normalized_input = self._normalize_city_name(city_input)
        logger.debug(
            f"Ищу город '{city_input}' (нормализовано: '{normalized_input}')")

        # Ищем точное совпадение по названию
        for city in cities:
            city_name = city.get('name', '')
            normalized_city = self._normalize_city_name(city_name)

            if normalized_city == normalized_input:
                city_code = city.get('id') or city.get('code')
                logger.info(
                    f"Найден точный код для города '{city_input}': {city_code}"
                )
                return str(city_code)

        # Ищем частичное совпадение
        for city in cities:
            city_name = city.get('name', '')
            normalized_city = self._normalize_city_name(city_name)

            if normalized_input in normalized_city or normalized_city in normalized_input:
                city_code = city.get('id') or city.get('code')
                logger.info(
                    f"Найден частичный код для города '{city_input}' -> '{city_name}': {city_code}"
                )
                return str(city_code)

        logger.warning(
            f"Код для города '{city_input}' не найден в базе TOP-EX")
        return None

    async def _perform_calculation(self, origin_code: str,
                                   destination_code: str,
                                   weight: float) -> Dict[str, Any]:
        """
        Выполняет фактический расчет стоимости доставки.
        
        Args:
            origin_code (str): Код города отправления
            destination_code (str): Код города назначения
            weight (float): Вес в килокилограммах
            
        Returns:
            Dict[str, Any]: Результат расчета
        """
        try:
            await self._ensure_session()

            calc_url = f"{self._base_url}/cse/calc"
            params = {
                'authToken': self._auth_token,
                'from': origin_code,
                'to': destination_code,
                'weight': weight
            }

            logger.debug(
                f"Выполняю расчет: {origin_code} -> {destination_code}, {weight}кг"
            )

            async with self._session.get(calc_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if data and data.get('status'):
                        # Обрабатываем успешный ответ с предложениями
                        offers = self._parse_shipping_offers(
                            data.get('data', []), weight)

                        # Находим самое дешевое предложение
                        cheapest_offer = min(
                            offers, key=lambda x: x.price) if offers else None

                        return {
                            'success':
                            True,
                            'offers': [offer.to_dict() for offer in offers],
                            'cheapest_offer':
                            cheapest_offer.to_dict()
                            if cheapest_offer else None,
                            'offers_count':
                            len(offers)
                        }
                    else:
                        error_msg = data.get('error', 'Неизвестная ошибка API')
                        return self._create_error_result(
                            "Ошибка API", error_msg)
                else:
                    return self._create_error_result(
                        "HTTP ошибка", f"Код ответа: {response.status}")

        except Exception as e:
            logger.error(f"Ошибка выполнения расчета: {e}")
            return self._create_error_result("Исключение", str(e))

    def _parse_shipping_offers(self, api_data: List[Dict],
                               weight: float) -> List[ShippingOffer]:
        """
        Парсит данные API в объекты ShippingOffer.
        
        Args:
            api_data (List[Dict]): Данные от API
            weight (int): Вес груза
            
        Returns:
            List[ShippingOffer]: Список предложений
        """
        offers = []

        for item in api_data:
            try:
                offer = ShippingOffer(
                    company_name=item.get('deliveryCompany',
                                          'Неизвестная компания'),
                    price=float(item.get('price', 0)),
                    delivery_days=int(item.get('deliveryTime', 0)),
                    tariff_name=item.get('tariffName', 'Стандартный тариф'),
                    weight=int(weight *
                               1000),  # Конвертируем кг в граммы для модели
                    additional_info={
                        'tariff_id': item.get('tariffId'),
                        'company_id': item.get('deliveryCompanyId'),
                        'raw_data': item
                    })
                offers.append(offer)
                logger.debug(
                    f"Добавлено предложение: {offer.company_name} - {offer.price}₽"
                )

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Ошибка парсинга предложения: {e}, данные: {item}")
                continue

        logger.info(
            f"Распарсено {len(offers)} предложений из {len(api_data)} элементов"
        )
        return offers

    async def _get_cached_cities(self) -> List[Dict[str, str]]:
        """
        Получает список городов с кешированием.
        
        Returns:
            List[Dict[str, str]]: Список городов
        """
        current_time = time.time()

        # Проверяем актуальность кеша
        if (self._cities_cache is not None
                and self._cities_cache_expires_at is not None
                and current_time < self._cities_cache_expires_at):
            logger.debug(
                f"Использую кешированный список городов ({len(self._cities_cache)} городов)"
            )
            return self._cities_cache

        # Обновляем кеш
        logger.info("Обновляю кеш списка городов из API TOP-EX")
        cities = await self.get_available_cities()

        if cities:
            self._cities_cache = cities
            self._cities_cache_expires_at = current_time + self._cities_cache_ttl
            logger.info(
                f"Кеш городов обновлен: {len(cities)} городов, TTL: {self._cities_cache_ttl}с"
            )
        else:
            logger.error("Не удалось обновить кеш городов")
            # Возвращаем старый кеш если он есть
            if self._cities_cache is not None:
                logger.info("Использую устаревший кеш городов")
                return self._cities_cache

        return cities or []

    def _normalize_city_name(self, city_name: str) -> str:
        """
        Нормализует название города для поиска.
        
        Убирает лишние пробелы, приводит к нижнему регистру,
        обрабатывает типичные сокращения и варианты написания.
        
        Args:
            city_name (str): Исходное название города
            
        Returns:
            str: Нормализованное название
        """
        if not city_name:
            return ""

        # Приводим к нижнему регистру и убираем лишние пробелы
        normalized = city_name.strip().lower()

        # Словарь замен для типичных сокращений и альтернативных написаний
        replacements = {
            'спб': 'санкт-петербург',
            'санкт петербург': 'санкт-петербург',
            'с-петербург': 'санкт-петербург',
            'с.петербург': 'санкт-петербург',
            'питер': 'санкт-петербург',
            'нижний новгород': 'н.новгород',
            'н новгород': 'н.новгород',
            'ростов-на-дону': 'ростов на дону',
            'ростов на дону': 'ростов-на-дону'
        }

        # Применяем замены
        for old, new in replacements.items():
            if old in normalized:
                normalized = normalized.replace(old, new)
                break

        return normalized

    def _create_error_result(self, error_type: str,
                             error_message: str) -> Dict[str, Any]:
        """
        Создает стандартный объект ошибки.
        
        Args:
            error_type (str): Тип ошибки
            error_message (str): Сообщение об ошибке
            
        Returns:
            Dict[str, Any]: Объект ошибки
        """
        return {
            'success': False,
            'error_type': error_type,
            'error': error_message,
            'offers': [],
            'cheapest_offer': None,
            'offers_count': 0
        }
