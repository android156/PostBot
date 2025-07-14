#!/usr/bin/env python3
"""
Test root endpoint with different parameters to find shipping calculation method.
"""
import asyncio
import aiohttp
import json
from config import Config

async def test_root_endpoint():
    """Test root endpoint with various parameters."""
    config = Config()
    
    async with aiohttp.ClientSession() as session:
        # Authenticate first
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
                    
                    # Test root endpoint with various parameters
                    origin_code = "cf862f89-442d-11dc-9497-0015170f8c09"  # Астрахань
                    destination_code = "cf862f6c-442d-11dc-9497-0015170f8c09"  # Пенза
                    
                    test_params = [
                        # Basic calculation parameters
                        {
                            'authToken': auth_token,
                            'method': 'calculate',
                            'origin': origin_code,
                            'destination': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'action': 'calculate',
                            'from': origin_code,
                            'to': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'service': 'calculate',
                            'cityFrom': origin_code,
                            'cityTo': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'type': 'express',
                            'method': 'calculate',
                            'origin': origin_code,
                            'destination': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'command': 'calculate',
                            'from_city': origin_code,
                            'to_city': destination_code,
                            'weight': 500
                        },
                        # Try with different action names
                        {
                            'authToken': auth_token,
                            'action': 'tariff',
                            'origin': origin_code,
                            'destination': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'method': 'price',
                            'from': origin_code,
                            'to': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'service': 'delivery',
                            'cityFrom': origin_code,
                            'cityTo': destination_code,
                            'weight': 500
                        }
                    ]
                    
                    print("\n🔍 Testing root endpoint with different parameters:")
                    
                    for i, params in enumerate(test_params):
                        print(f"\n--- Test {i+1} ---")
                        print(f"Parameters: {json.dumps(params, indent=2, ensure_ascii=False)}")
                        
                        try:
                            async with session.get(config.topex_api_base, params=params, timeout=10) as resp:
                                print(f"Status: {resp.status}")
                                
                                if resp.status == 200:
                                    data = await resp.json()
                                    print(f"✅ SUCCESS! Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                    
                                    # If this works, let's try more variations
                                    if data.get('status'):
                                        print("🎉 Found working endpoint!")
                                        return
                                else:
                                    text = await resp.text()
                                    print(f"Response: {text}")
                                    
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            
                    # Also try POST requests to root
                    print("\n🔍 Testing POST requests to root endpoint:")
                    
                    post_data_sets = [
                        {
                            'authToken': auth_token,
                            'method': 'calculate',
                            'origin': origin_code,
                            'destination': destination_code,
                            'weight': 500
                        },
                        {
                            'authToken': auth_token,
                            'action': 'calculate',
                            'from': origin_code,
                            'to': destination_code,
                            'weight': 500
                        }
                    ]
                    
                    for i, data_set in enumerate(post_data_sets):
                        print(f"\n--- POST Test {i+1} ---")
                        print(f"Data: {json.dumps(data_set, indent=2, ensure_ascii=False)}")
                        
                        try:
                            async with session.post(config.topex_api_base, json=data_set, timeout=10) as resp:
                                print(f"Status: {resp.status}")
                                
                                if resp.status == 200:
                                    data = await resp.json()
                                    print(f"✅ SUCCESS! Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                    
                                    if data.get('status'):
                                        print("🎉 Found working POST endpoint!")
                                        return
                                else:
                                    text = await resp.text()
                                    print(f"Response: {text}")
                                    
                        except Exception as e:
                            print(f"❌ Error: {e}")
                            
                else:
                    print("❌ Authentication failed")
            else:
                print(f"❌ Authentication request failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_root_endpoint())