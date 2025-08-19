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
        api_parameters = self._config.get_api_parameters()

        self._email = api_credentials['email']
        self._password = api_credentials['password']
        self._base_url = api_credentials['base_url']
        self._timeout = api_settings['timeout']
        self._retry_count = api_settings['retry_count']
        self._rate_limit_delay = api_settings['rate_limit_delay']
        
        # Статичные параметры API
        self._user_id = api_parameters['user_id']
        self._cargo_type = api_parameters['cargo_type']
        self._cargo_seats_number = api_parameters['cargo_seats_number']
        self._delivery_method = api_parameters['delivery_method']

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
            return await self._calculate_with_codes(origin_code, destination_code, weight)

        except Exception as e:
            logger.error(f"Ошибка расчета стоимости доставки: {e}")
            return self._create_error_result("Ошибка расчета", str(e))

    async def calculate_shipping_cost_with_codes(self, origin_code: str, destination_code: str,
                                               weight: float) -> Dict[str, Any]:
        """
        Рассчитывает стоимость доставки с готовыми кодами городов.
        
        Оптимизированный метод для случаев, когда коды городов уже получены.
        Не выполняет резолв кодов, сразу переходит к расчету.
        
        Args:
            origin_code (str): Код города отправления
            destination_code (str): Код города назначения
            weight (float): Вес груза в килокилограммах
            
        Returns:
            Dict[str, Any]: Результат расчета с предложениями
        """
        try:
            logger.debug(f"Прямой расчет с кодами: {origin_code} -> {destination_code}, {weight}кг")
            
            # Валидация кодов городов
            if not origin_code or not destination_code:
                missing_codes = []
                if not origin_code:
                    missing_codes.append("отправления")
                if not destination_code:
                    missing_codes.append("назначения")

                return self._create_error_result(
                    "Отсутствуют коды городов",
                    f"Не переданы коды городов {', '.join(missing_codes)}")

            # Выполняем расчет стоимости напрямую
            return await self._calculate_with_codes(origin_code, destination_code, weight)

        except Exception as e:
            logger.error(f"Ошибка прямого расчета стоимости доставки: {e}")
            return self._create_error_result("Ошибка расчета", str(e))

    async def _calculate_with_codes(self, origin_code: str, destination_code: str,
                                  weight: float) -> Dict[str, Any]:
        """
        Внутренний метод для выполнения расчета с готовыми кодами.
        
        Args:
            origin_code (str): Код города отправления
            destination_code (str): Код города назначения
            weight (float): Вес груза в килокилограммах
            
        Returns:
            Dict[str, Any]: Результат расчета
        """
        # Выполняем расчет стоимости
        calculation_result = await self._perform_calculation(
            origin_code, destination_code, weight)

        # Добавляем задержку для соблюдения rate limit
        await asyncio.sleep(self._rate_limit_delay)

        return calculation_result

    async def get_available_cities(self, query: str = "") -> List[Dict[str, str]]:
        """
        Получает список доступных городов для доставки.
        
        Args:
            query (str): Название города или его часть для поиска
        
        Returns:
            List[Dict[str, str]]: Список городов с кодами
        """
        try:
            await self._ensure_session()

            cities_url = f"{self._base_url}/cse/cityList"
            
            # Согласно документации API - это GET запрос с параметрами в URL
            params = {
                'country_id': 'f2cd6487-4422-11dc-9497-0015170f8c09',  # Россия
                'query': query,  # Название города или его часть
                'pagination[pageSize]': 1000,  # Максимальное количество результатов
                'pagination[page]': 1  # Номер страницы (начинается с 1)
            }

            logger.debug(f"Запрашиваю список городов: GET {cities_url} с query='{query}'")

            async with self._session.get(cities_url, params=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data and response_data.get('status'):
                        # API возвращает данные в формате {"id": "name"} в поле items
                        items = response_data.get('items', {})
                        # Преобразуем в список словарей для совместимости
                        cities = [{"id": city_id, "name": city_name} 
                                for city_id, city_name in items.items()]
                        logger.info(f"Получено {len(cities)} городов из API по запросу '{query}'")
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
        
        Если передан код (UUID или числовая строка), возвращает его как есть.
        Если передано название, ищет код через API TOP-EX.
        
        Args:
            city_input (str): Название или код города
            
        Returns:
            Optional[str]: Код города или None если не найден
        """
        # Проверяем, не является ли входная строка уже кодом (UUID или числовая строка)
        if city_input.isdigit():
            logger.debug(f"Получен числовой код города: {city_input}")
            return city_input
        
        # Проверяем, не является ли это UUID (формат: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        if len(city_input) == 36 and city_input.count('-') == 4:
            # Дополнительная проверка на валидность UUID
            parts = city_input.split('-')
            if (len(parts) == 5 and 
                len(parts[0]) == 8 and len(parts[1]) == 4 and len(parts[2]) == 4 and 
                len(parts[3]) == 4 and len(parts[4]) == 12):
                logger.debug(f"Получен UUID код города: {city_input}")
                return city_input

        # Нормализуем название для поиска
        normalized_input = self._normalize_city_name(city_input)
        logger.debug(f"Ищу город '{city_input}' (нормализовано: '{normalized_input}')")

        # Сначала попробуем точный поиск
        cities = await self._get_cached_cities(city_input)
        if cities:
            # Ищем точное совпадение
            for city in cities:
                city_name = city.get('name', '')
                normalized_city = self._normalize_city_name(city_name)

                if normalized_city == normalized_input:
                    city_code = city.get('id') or city.get('code')
                    logger.info(f"Найден точный код для города '{city_input}': {city_code}")
                    return str(city_code)

            # Если точного совпадения нет, берем первый результат
            city = cities[0]
            city_code = city.get('id') or city.get('code')
            city_name = city.get('name', '')
            logger.info(f"Найден код для города '{city_input}' -> '{city_name}': {city_code}")
            return str(city_code)

        # Если ничего не найдено через прямой поиск, попробуем общий кеш
        logger.debug("Поиск в общем кеше городов")
        all_cities = await self._get_cached_cities("")
        if not all_cities:
            logger.error("Не удалось получить список городов для поиска")
            return None

        # Ищем точное совпадение в общем кеше
        for city in all_cities:
            city_name = city.get('name', '')
            normalized_city = self._normalize_city_name(city_name)

            if normalized_city == normalized_input:
                city_code = city.get('id') or city.get('code')
                logger.info(f"Найден точный код в кеше для города '{city_input}': {city_code}")
                return str(city_code)

        # Ищем частичное совпадение в общем кеше
        for city in all_cities:
            city_name = city.get('name', '')
            normalized_city = self._normalize_city_name(city_name)

            if normalized_input in normalized_city or normalized_city in normalized_input:
                city_code = city.get('id') or city.get('code')
                logger.info(f"Найден частичный код в кеше для города '{city_input}' -> '{city_name}': {city_code}")
                return str(city_code)

        logger.warning(f"Код для города '{city_input}' не найден в базе TOP-EX")
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
            # Параметры запроса из конфигурации
            params = {
                'attributes[user_id]': self._user_id,
                'attributes[sender_city]': origin_code,
                'attributes[recipient_city]': destination_code,
                'attributes[cargo_type]': self._cargo_type,
                'attributes[cargo_seats_number]': self._cargo_seats_number,
                'attributes[cargo_weight]': str(weight),  # Вес в кг
                'attributes[delivery_method]': self._delivery_method  # 1 = доставка до дверей
            }

            logger.info(
                f"Выполняю расчет стоимости: {origin_code} -> {destination_code}, {weight}кг"
            )
            logger.debug(f"URL: {calc_url}")
            logger.debug(f"Параметры: {params}")

            async with self._session.get(calc_url, params=params) as response:
                logger.info(f"Получен ответ от API расчета: статус {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Данные ответа API: {data}")

                    if data and data.get('status'):
                        # Обрабатываем успешный ответ с предложениями
                        api_data = data.get('data', [])
                        logger.info(f"API вернул {len(api_data)} предложений")
                        
                        offers = self._parse_shipping_offers(api_data, weight)
                        logger.info(f"Обработано {len(offers)} предложений")

                        # Находим самое дешевое предложение
                        cheapest_offer = min(
                            offers, key=lambda x: x.price) if offers else None

                        if cheapest_offer:
                            logger.info(f"Лучшее предложение: {cheapest_offer.company_name} - {cheapest_offer.price}₽")

                        return {
                            'success': True,
                            'offers': [offer.to_dict() for offer in offers],
                            'cheapest_offer': cheapest_offer.to_dict() if cheapest_offer else None,
                            'offers_count': len(offers)
                        }
                    else:
                        error_msg = data.get('error', 'Неизвестная ошибка API')
                        logger.error(f"API вернул ошибку: {error_msg}")
                        return self._create_error_result("Ошибка API", error_msg)
                else:
                    response_text = await response.text()
                    logger.error(f"HTTP ошибка {response.status}: {response_text}")
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
            weight (float): Вес груза в килограммах
            
        Returns:
            List[ShippingOffer]: Список предложений
        """
        offers = []

        for item in api_data:
            try:
                # Извлекаем данные согласно реальной структуре API
                company_name = item.get('deliveryCompanyLabel', 'Неизвестная компания')
                
                # Используем user_price как основную цену, если нет - берем retailPrice
                price = item.get('user_price')
                if price is None:
                    price = item.get('retailPrice')
                
                # Пропускаем предложения с неопределенной ценой
                if price is None:
                    logger.debug(f"Пропускаю предложение {company_name} - цена не определена")
                    continue
                
                # Срок доставки из totalDeliveryDaysCount
                delivery_days = item.get('totalDeliveryDaysCount')
                if delivery_days is None:
                    # Пробуем получить из deliveryDaysCount
                    delivery_days = item.get('deliveryDaysCount')
                
                # Если сроки доставки не определены, используем специальное значение -1 для "по запросу"
                if delivery_days is None:
                    delivery_days = -1
                    logger.debug(f"Срок доставки для {company_name} не определен, установлен как 'по запросу'")
                else:
                    # Преобразуем в int только если значение не None
                    try:
                        delivery_days = int(delivery_days)
                    except (ValueError, TypeError):
                        delivery_days = -1
                        logger.debug(f"Не удалось преобразовать срок доставки '{delivery_days}' для {company_name}, установлен как 'по запросу'")
                
                # Название тарифа
                tariff_name = item.get('tariffName', 'Стандартный тариф')
                
                # Дополнительная информация о способе доставки
                delivery_method_label = item.get('deliveryMethodLabel', '')
                if delivery_method_label:
                    tariff_display = f"{tariff_name} ({delivery_method_label})"
                else:
                    tariff_display = tariff_name

                offer = ShippingOffer(
                    company_name=company_name,
                    price=float(price),
                    delivery_days=delivery_days,  # Уже int или -1
                    tariff_name=tariff_display,
                    weight=int(weight * 1000),  # Конвертируем кг в граммы для модели
                    additional_info={
                        'tariff_id': item.get('tariffId'),
                        'delivery_company_id': item.get('deliveryCompany'),
                        'delivery_method': item.get('deliveryMethod'),
                        'delivery_method_label': item.get('deliveryMethodLabel'),
                        'retail_price': item.get('retailPrice'),
                        'user_price_without_discount': item.get('user_price_without_discount'),
                        'active_discount': item.get('activeDiscount'),
                        'min_period': item.get('minPeriod'),
                        'max_period': item.get('maxPeriod'),
                        'pickup_days_count': item.get('pickupDaysCount'),
                        'delivery_days_count': item.get('deliveryDaysCount'),
                        'sort': item.get('sort'),
                        'period_sort': item.get('periodSort'),
                        'delivery_company_icon': item.get('deliveryCompanyIcon'),
                        'raw_data': item
                    })
                offers.append(offer)
                logger.debug(
                    f"Добавлено предложение: {offer.company_name} - {offer.tariff_name} - {offer.price}₽ за {offer.delivery_days} дн."
                )

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Ошибка парсинга предложения: {e}, данные: {item}")
                continue

        logger.info(
            f"Распарсено {len(offers)} предложений из {len(api_data)} элементов"
        )
        
        # Применяем фильтр категорий доставки
        delivery_filter = self._config.get_delivery_filter()
        if delivery_filter:
            original_count = len(offers)
            filtered_offers = []
            
            logger.info(f"🔍 Применяю фильтр доставки: {delivery_filter}")
            
            for offer in offers:
                delivery_method_label = offer.additional_info.get('delivery_method_label', '')
                # Проверяем, содержит ли метка доставки одно из разрешенных значений
                if any(filter_term in delivery_method_label for filter_term in delivery_filter):
                    filtered_offers.append(offer)
                    logger.debug(f"✅ Прошло фильтр: {offer.company_name} - {delivery_method_label}")
                else:
                    logger.debug(f"❌ Отфильтровано: {offer.company_name} - {delivery_method_label}")
            
            offers = filtered_offers
            filtered_count = len(offers)
            
            if filtered_count < original_count:
                logger.info(f"📊 Фильтрация завершена: {original_count} → {filtered_count} предложений (удалено {original_count - filtered_count})")
            else:
                logger.info(f"📊 Фильтрация не изменила количество предложений: {filtered_count}")
        else:
            logger.debug("Фильтр доставки не настроен, используются все предложения")
        
        # Логирование предложений (детальное или краткое)
        if offers:
            # Сортируем предложения по цене для анализа
            sorted_offers = sorted(offers, key=lambda x: x.price)
            best_offer = sorted_offers[0]
            
            # Проверяем настройку детального логирования
            detailed_log = self._config.get_detailed_log()
            
            if detailed_log:
                # Детальное логирование (как было раньше)
                logger.info(f"═══ ДЕТАЛЬНЫЙ СПИСОК ПРЕДЛОЖЕНИЙ ДЛЯ ВЕСА {weight}КГ ═══")
                
                # Статистика
                prices = [offer.price for offer in sorted_offers]
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                
                logger.info(f"📊 Статистика: {len(offers)} предложений, цены от {min_price}₽ до {max_price}₽ (среднее: {avg_price:.2f}₽)")
                
                # Топ-5 самых дешевых предложений
                logger.info("🏆 ТОП-5 САМЫХ ДЕШЕВЫХ ПРЕДЛОЖЕНИЙ:")
                for i, offer in enumerate(sorted_offers[:5], 1):
                    status = "⭐ ВЫБРАНО" if i == 1 else f"  #{i}"
                    logger.info(f"{status} | {offer.company_name} | {offer.price}₽ | {offer.delivery_days}дн | {offer.tariff_name}")
                
                # Все остальные предложения (если их больше 5)
                if len(sorted_offers) > 5:
                    logger.info(f"📋 ОСТАЛЬНЫЕ ПРЕДЛОЖЕНИЯ ({len(sorted_offers) - 5}):")
                    for i, offer in enumerate(sorted_offers[5:], 6):
                        logger.info(f"  #{i} | {offer.company_name} | {offer.price}₽ | {offer.delivery_days}дн | {offer.tariff_name}")
                
                logger.info(f"══════════════════════════════════════════════════════════")
            else:
                # Краткое логирование - одна строка с лучшим предложением
                logger.info(f"📦 {weight}кг → {best_offer.company_name} | {best_offer.price}₽ | {best_offer.delivery_days}дн | {best_offer.tariff_name}")
        else:
            logger.warning(f"❌ Нет предложений для веса {weight}кг")
        
        return offers

    async def _get_cached_cities(self, query: str = "") -> List[Dict[str, str]]:
        """
        Получает список городов с кешированием.
        
        Args:
            query (str): Название города или его часть для поиска
        
        Returns:
            List[Dict[str, str]]: Список городов
        """
        current_time = time.time()

        # Если запрос пустой, используем общий кеш
        if not query:
            # Проверяем актуальность общего кеша
            if (self._cities_cache is not None
                    and self._cities_cache_expires_at is not None
                    and current_time < self._cities_cache_expires_at):
                logger.debug(
                    f"Использую кешированный список городов ({len(self._cities_cache)} городов)"
                )
                return self._cities_cache

            # Обновляем общий кеш
            logger.info("Обновляю общий кеш списка городов из API TOP-EX")
            cities = await self.get_available_cities("")

            if cities:
                self._cities_cache = cities
                self._cities_cache_expires_at = current_time + self._cities_cache_ttl
                logger.info(
                    f"Общий кеш городов обновлен: {len(cities)} городов, TTL: {self._cities_cache_ttl}с"
                )
            else:
                logger.error("Не удалось обновить общий кеш городов")
                # Возвращаем старый кеш если он есть
                if self._cities_cache is not None:
                    logger.info("Использую устаревший общий кеш городов")
                    return self._cities_cache

            return cities or []
        else:
            # Для конкретных запросов не кешируем, делаем прямой запрос
            logger.info(f"Выполняю поиск городов по запросу: '{query}'")
            return await self.get_available_cities(query)

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
