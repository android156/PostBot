#!/usr/bin/env python3
"""
Test script to find correct TOP-EX API endpoints for shipping calculations.
"""
import asyncio
import aiohttp
import json
from config import Config

async def test_api_endpoints():
    """Test various API endpoints to find the shipping calculation endpoint."""
    config = Config()
    
    # First authenticate
    async with aiohttp.ClientSession() as session:
        auth_url = f"{config.topex_api_base}/auth"
        params = {
            'email': config.topex_email,
            'password': config.topex_password
        }
        
        print("Authenticating...")
        async with session.get(auth_url, params=params) as response:
            if response.status == 200:
                auth_data = await response.json()
                if auth_data.get('status'):
                    auth_token = auth_data.get('authToken')
                    print(f"✅ Authenticated successfully")
                    
                    # Test city codes
                    origin_code = "cf862f89-442d-11dc-9497-0015170f8c09"  # Астрахань
                    destination_code = "cf862f6c-442d-11dc-9497-0015170f8c09"  # Пенза
                    weight = 500
                    
                    # Test different endpoints
                    test_endpoints = [
                        "/express/calculateDelivery",
                        "/express/calculate", 
                        "/shipping/calculate",
                        "/delivery/calculate",
                        "/calculate",
                        "/express/tariff",
                        "/express/price",
                        "/express/cost",
                        "/tariff/calculate",
                        "/price/calculate",
                        "/express/delivery",
                        "/delivery/price",
                        "/express/rates",
                        "/rates/calculate"
                    ]
                    
                    for endpoint in test_endpoints:
                        print(f"\n🔍 Testing endpoint: {endpoint}")
                        test_url = f"{config.topex_api_base}{endpoint}"
                        
                        # Try different parameter combinations
                        param_sets = [
                            {
                                'authToken': auth_token,
                                'origin': origin_code,
                                'destination': destination_code,
                                'weight': weight
                            },
                            {
                                'authToken': auth_token,
                                'from': origin_code,
                                'to': destination_code,
                                'weight': weight
                            },
                            {
                                'authToken': auth_token,
                                'cityFrom': origin_code,
                                'cityTo': destination_code,
                                'weight': weight
                            },
                            {
                                'authToken': auth_token,
                                'fromCity': origin_code,
                                'toCity': destination_code,
                                'weight': weight
                            }
                        ]
                        
                        for i, params in enumerate(param_sets):
                            try:
                                async with session.get(test_url, params=params, timeout=10) as resp:
                                    print(f"  Params set {i+1}: Status {resp.status}")
                                    if resp.status == 200:
                                        data = await resp.json()
                                        print(f"  ✅ Success! Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                        return
                                    elif resp.status == 404:
                                        print(f"  ❌ Not found (404)")
                                        break
                                    else:
                                        text = await resp.text()
                                        print(f"  ⚠️  Status {resp.status}: {text[:200]}...")
                            except Exception as e:
                                print(f"  ❌ Error: {e}")
                                
                else:
                    print("❌ Authentication failed")
            else:
                print(f"❌ Authentication request failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())