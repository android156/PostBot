#!/usr/bin/env python3
"""
Test script to verify the new /cse/calc endpoint with real parameters.
"""
import asyncio
import aiohttp
import json
from config import Config

async def test_new_endpoint():
    """Test the new /cse/calc endpoint with real parameters."""
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
                    print(f"   Токен: {auth_token[:20]}...")
                    
                    # Step 2: Test the new endpoint
                    print("\n💰 Тестирование нового endpoint...")
                    calc_url = "https://lk.top-ex.ru/api/cse/calc"
                    
                    # Тестовые параметры
                    test_params = {
                        'authToken': auth_token,
                        'attributes[user_id]': '14',
                        'attributes[sender_city]': 'cf862f89-442d-11dc-9497-0015170f8c09',  # Астрахань
                        'attributes[recipient_city]': 'cf862f6c-442d-11dc-9497-0015170f8c09',  # Пенза
                        'attributes[cargo_type]': '4aab1fc6-fc2b-473a-8728-58bcd4ff79ba',  # Груз
                        'attributes[cargo_seats_number]': '1',
                        'attributes[cargo_weight]': '500'
                    }
                    
                    print(f"📡 Запрос к: {calc_url}")
                    print(f"📊 Параметры:")
                    for key, value in test_params.items():
                        print(f"   {key}: {value}")
                    
                    async with session.get(calc_url, params=test_params, timeout=30) as calc_response:
                        print(f"\n📈 Ответ API: статус {calc_response.status}")
                        
                        if calc_response.status == 200:
                            calc_data = await calc_response.json()
                            print(f"✅ Данные получены:")
                            print(json.dumps(calc_data, indent=2, ensure_ascii=False))
                            
                            if calc_data.get('status'):
                                print(f"\n🎉 УСПЕХ! API вернул данные о стоимости")
                            else:
                                print(f"\n⚠️  API вернул ошибку: {calc_data.get('error', 'Неизвестная ошибка')}")
                        else:
                            error_text = await calc_response.text()
                            print(f"❌ HTTP ошибка {calc_response.status}: {error_text[:200]}")
                            
                else:
                    print(f"❌ Ошибка аутентификации: {auth_data.get('error', 'Неизвестная ошибка')}")
            else:
                print(f"❌ Ошибка запроса аутентификации: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_new_endpoint())