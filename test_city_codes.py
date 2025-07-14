#!/usr/bin/env python3
"""
Test script to find correct city codes from the address book.
"""
import asyncio
import aiohttp
import json
from config import Config

async def test_city_codes():
    """Test to find correct city codes from the address book."""
    config = Config()
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Authenticate
        auth_url = "https://lk.top-ex.ru/api/auth"
        auth_params = {
            'email': config.topex_email,
            'password': config.topex_password
        }
        
        print("🔑 Аутентификация...")
        async with session.get(auth_url, params=auth_params) as response:
            if response.status == 200:
                auth_data = await response.json()
                if auth_data.get('status'):
                    auth_token = auth_data.get('authToken')
                    print(f"✅ Аутентификация успешна")
                    
                    # Step 2: Get address book entries to find city codes
                    print("\n📖 Получение адресной книги...")
                    address_url = "https://lk.top-ex.ru/api/addressBook/list"
                    address_params = {
                        'authToken': auth_token,
                        'type': 'express',
                        'pageSize': 20  # Получим больше записей
                    }
                    
                    async with session.get(address_url, params=address_params) as addr_response:
                        if addr_response.status == 200:
                            addr_data = await addr_response.json()
                            if addr_data.get('status') and addr_data.get('items'):
                                print(f"✅ Найдено {len(addr_data['items'])} записей")
                                
                                # Соберем уникальные коды городов
                                city_codes = set()
                                for item in addr_data['items']:
                                    city_code = item.get('city')
                                    if city_code:
                                        city_codes.add(city_code)
                                
                                print(f"📍 Найдено {len(city_codes)} уникальных кодов городов")
                                
                                # Попробуем первые два кода для тестирования
                                test_codes = list(city_codes)[:2]
                                if len(test_codes) >= 2:
                                    sender_code = test_codes[0]
                                    recipient_code = test_codes[1]
                                    
                                    print(f"\n🧪 Тестируем коды городов:")
                                    print(f"   Отправитель: {sender_code}")
                                    print(f"   Получатель: {recipient_code}")
                                    
                                    # Step 3: Test calculation with real city codes
                                    calc_url = "https://lk.top-ex.ru/api/cse/calc"
                                    test_params = {
                                        'authToken': auth_token,
                                        'attributes[user_id]': '14',
                                        'attributes[sender_city]': sender_code,
                                        'attributes[recipient_city]': recipient_code,
                                        'attributes[cargo_type]': '4aab1fc6-fc2b-473a-8728-58bcd4ff79ba',
                                        'attributes[cargo_seats_number]': '1',
                                        'attributes[cargo_weight]': '500'
                                    }
                                    
                                    print(f"\n💰 Тестирование расчета стоимости...")
                                    async with session.get(calc_url, params=test_params, timeout=30) as calc_response:
                                        print(f"📈 Ответ API: статус {calc_response.status}")
                                        
                                        if calc_response.status == 200:
                                            calc_data = await calc_response.json()
                                            print(f"✅ Данные получены:")
                                            print(json.dumps(calc_data, indent=2, ensure_ascii=False))
                                            
                                            if calc_data.get('status'):
                                                print(f"\n🎉 УСПЕХ! API вернул данные о стоимости")
                                                return True
                                            else:
                                                print(f"\n⚠️  API вернул ошибку: {calc_data.get('error', calc_data.get('errors', 'Неизвестная ошибка'))}")
                                        else:
                                            error_text = await calc_response.text()
                                            print(f"❌ HTTP ошибка {calc_response.status}: {error_text[:200]}")
                                else:
                                    print("❌ Нет данных в адресной книге")
                            else:
                                print(f"❌ Ошибка получения адресной книги: {addr_data.get('error', 'Неизвестная ошибка')}")
                        else:
                            print(f"❌ Ошибка запроса адресной книги: {addr_response.status}")
                else:
                    print(f"❌ Ошибка аутентификации: {auth_data.get('error', 'Неизвестная ошибка')}")
            else:
                print(f"❌ Ошибка запроса аутентификации: {response.status}")
    
    return False

if __name__ == "__main__":
    asyncio.run(test_city_codes())