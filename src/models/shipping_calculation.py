"""
Модели для результатов расчета стоимости доставки.

Содержит классы для представления результатов расчета стоимости доставки,
предложений от компаний и сводной информации.

Принципы SOLID:
- Single Responsibility Principle (SRP): Каждый класс отвечает за свой тип данных
- Open/Closed Principle (OCP): Легко добавлять новые типы предложений
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .route import Route


@dataclass
class ShippingOffer:
    """
    Модель предложения доставки от компании.
    
    Представляет одно предложение по доставке с ценой,
    сроками и информацией о компании.
    
    Attributes:
        company_name (str): Название транспортной компании
        price (float): Стоимость доставки в рублях
        delivery_days (int): Срок доставки в днях
        tariff_name (str): Название тарифа компании
        weight (int): Вес груза в граммах для этого предложения
        additional_info (Dict[str, Any]): Дополнительная информация
    """
    company_name: str
    price: float
    delivery_days: int
    tariff_name: str
    weight: int
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        Постобработка после инициализации.
        
        Проверяет корректность данных предложения.
        """
        if self.price < 0:
            raise ValueError("Стоимость доставки не может быть отрицательной")
        if self.delivery_days < 0:
            raise ValueError("Срок доставки не может быть отрицательным")
        if self.weight <= 0:
            raise ValueError("Вес должен быть положительным числом")
    
    def get_price_per_kg(self) -> float:
        """
        Рассчитывает стоимость доставки за килограмм.
        
        Returns:
            float: Стоимость за кг в рублях
        """
        weight_kg = self.weight / 1000
        return self.price / weight_kg if weight_kg > 0 else 0
    
    def is_better_than(self, other: 'ShippingOffer') -> bool:
        """
        Сравнивает это предложение с другим.
        
        Считает предложение лучше, если оно дешевле при том же весе.
        При одинаковой цене предпочитает быструю доставку.
        
        Args:
            other (ShippingOffer): Другое предложение для сравнения
            
        Returns:
            bool: True если это предложение лучше
        """
        if self.weight != other.weight:
            return False
            
        if self.price < other.price:
            return True
        elif self.price == other.price:
            return self.delivery_days < other.delivery_days
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертирует предложение в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными предложения
        """
        return {
            'company_name': self.company_name,
            'price': self.price,
            'delivery_days': self.delivery_days,
            'tariff_name': self.tariff_name,
            'weight': self.weight,
            'weight_kg': self.weight / 1000,
            'price_per_kg': self.get_price_per_kg(),
            'additional_info': self.additional_info
        }


@dataclass
class WeightCategoryResult:
    """
    Результат расчета для одной весовой категории.
    
    Содержит все предложения для определенного веса
    и информацию о самом выгодном предложении.
    
    Attributes:
        weight (int): Вес в граммах
        offers (List[ShippingOffer]): Все предложения для этого веса
        cheapest_offer (Optional[ShippingOffer]): Самое дешевое предложение
        calculation_error (Optional[str]): Ошибка расчета (если была)
    """
    weight: int
    offers: List[ShippingOffer] = field(default_factory=list)
    cheapest_offer: Optional[ShippingOffer] = None
    calculation_error: Optional[str] = None
    
    def __post_init__(self):
        """
        Постобработка - находит самое дешевое предложение.
        """
        if self.offers and not self.cheapest_offer:
            self.cheapest_offer = min(self.offers, key=lambda x: x.price)
    
    def add_offer(self, offer: ShippingOffer) -> None:
        """
        Добавляет предложение в результат.
        
        Args:
            offer (ShippingOffer): Предложение для добавления
        """
        if offer.weight != self.weight:
            raise ValueError(f"Вес предложения ({offer.weight}г) не соответствует категории ({self.weight}г)")
            
        self.offers.append(offer)
        
        # Обновляем самое дешевое предложение
        if not self.cheapest_offer or offer.price < self.cheapest_offer.price:
            self.cheapest_offer = offer
    
    def has_offers(self) -> bool:
        """
        Проверяет, есть ли предложения для этой категории.
        
        Returns:
            bool: True если есть предложения
        """
        return len(self.offers) > 0
    
    def get_weight_kg(self) -> float:
        """
        Возвращает вес в килограммах.
        
        Returns:
            float: Вес в кг
        """
        return self.weight / 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертирует результат в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными результата
        """
        return {
            'weight': self.weight,
            'weight_kg': self.get_weight_kg(),
            'offers_count': len(self.offers),
            'offers': [offer.to_dict() for offer in self.offers],
            'cheapest_offer': self.cheapest_offer.to_dict() if self.cheapest_offer else None,
            'calculation_error': self.calculation_error,
            'has_offers': self.has_offers()
        }


@dataclass
class RouteCalculationResult:
    """
    Результат расчета стоимости доставки для одного маршрута.
    
    Содержит результаты для всех весовых категорий
    и общую информацию о расчете.
    
    Attributes:
        route (Route): Маршрут доставки
        weight_results (Dict[int, WeightCategoryResult]): Результаты по весам
        calculation_time (datetime): Время выполнения расчета
        total_offers (int): Общее количество предложений
        successful_weights (List[int]): Веса с успешными расчетами
    """
    route: Route
    weight_results: Dict[int, WeightCategoryResult] = field(default_factory=dict)
    calculation_time: datetime = field(default_factory=datetime.now)
    total_offers: int = 0
    successful_weights: List[int] = field(default_factory=list)
    
    def add_weight_result(self, weight_result: WeightCategoryResult) -> None:
        """
        Добавляет результат расчета для весовой категории.
        
        Args:
            weight_result (WeightCategoryResult): Результат для веса
        """
        weight = weight_result.weight
        self.weight_results[weight] = weight_result
        
        if weight_result.has_offers():
            self.successful_weights.append(weight)
            self.total_offers += len(weight_result.offers)
    
    def get_all_cheapest_offers(self) -> List[ShippingOffer]:
        """
        Возвращает самые дешевые предложения для всех весов.
        
        Returns:
            List[ShippingOffer]: Список самых выгодных предложений
        """
        cheapest_offers = []
        for weight_result in self.weight_results.values():
            if weight_result.cheapest_offer:
                cheapest_offers.append(weight_result.cheapest_offer)
        return cheapest_offers
    
    def get_best_weight_category(self) -> Optional[int]:
        """
        Находит весовую категорию с самым выгодным предложением.
        
        Returns:
            Optional[int]: Вес в граммах с лучшим соотношением цена/кг
        """
        if not self.weight_results:
            return None
            
        best_weight = None
        best_price_per_kg = float('inf')
        
        for weight, result in self.weight_results.items():
            if result.cheapest_offer:
                price_per_kg = result.cheapest_offer.get_price_per_kg()
                if price_per_kg < best_price_per_kg:
                    best_price_per_kg = price_per_kg
                    best_weight = weight
                    
        return best_weight
    
    def is_successful(self) -> bool:
        """
        Проверяет, был ли расчет успешным.
        
        Returns:
            bool: True если есть хотя бы одно предложение
        """
        return len(self.successful_weights) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертирует результат в словарь.
        
        Returns:
            Dict[str, Any]: Полный словарь с результатами
        """
        return {
            'route': self.route.to_dict(),
            'calculation_time': self.calculation_time.isoformat(),
            'total_offers': self.total_offers,
            'successful_weights': self.successful_weights,
            'successful_weights_count': len(self.successful_weights),
            'weight_results': {
                weight: result.to_dict() 
                for weight, result in self.weight_results.items()
            },
            'all_cheapest_offers': [
                offer.to_dict() for offer in self.get_all_cheapest_offers()
            ],
            'best_weight_category': self.get_best_weight_category(),
            'is_successful': self.is_successful()
        }