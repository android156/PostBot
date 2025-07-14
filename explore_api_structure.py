#!/usr/bin/env python3
"""
Explore TOP-EX API structure to find available endpoints.
"""
import asyncio
import aiohttp
import json
from config import Config

async def explore_api():
    """Explore API structure to find available endpoints."""
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
                    
                    # Check what endpoints are available by trying common paths
                    base_endpoints = [
                        "/",
                        "/express",
                        "/express/",
                        "/express/list",
                        "/express/methods",
                        "/express/services",
                        "/express/companies",
                        "/express/tariffs",
                        "/express/info",
                        "/api",
                        "/api/",
                        "/api/express",
                        "/api/calculate",
                        "/methods",
                        "/services",
                        "/companies",
                        "/tariffs",
                        "/info",
                        "/help",
                        "/express/help"
                    ]
                    
                    print("\n🔍 Exploring available endpoints:")
                    
                    for endpoint in base_endpoints:
                        test_url = f"{config.topex_api_base}{endpoint}"
                        
                        try:
                            async with session.get(test_url, params={'authToken': auth_token}, timeout=10) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    print(f"  ✅ {endpoint}: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")
                                elif resp.status == 404:
                                    print(f"  ❌ {endpoint}: Not found")
                                else:
                                    text = await resp.text()
                                    print(f"  ⚠️  {endpoint}: Status {resp.status} - {text[:100]}...")
                        except Exception as e:
                            print(f"  ❌ {endpoint}: Error - {e}")
                    
                    # Also try POST requests for calculation
                    print("\n🔍 Testing POST requests:")
                    post_endpoints = [
                        "/express/calculate",
                        "/express/calculateDelivery",
                        "/calculate",
                        "/api/calculate"
                    ]
                    
                    for endpoint in post_endpoints:
                        test_url = f"{config.topex_api_base}{endpoint}"
                        
                        test_data = {
                            'authToken': auth_token,
                            'origin': "cf862f89-442d-11dc-9497-0015170f8c09",
                            'destination': "cf862f6c-442d-11dc-9497-0015170f8c09",
                            'weight': 500
                        }
                        
                        try:
                            async with session.post(test_url, json=test_data, timeout=10) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    print(f"  ✅ POST {endpoint}: {json.dumps(data, indent=2, ensure_ascii=False)}")
                                elif resp.status == 404:
                                    print(f"  ❌ POST {endpoint}: Not found")
                                else:
                                    text = await resp.text()
                                    print(f"  ⚠️  POST {endpoint}: Status {resp.status} - {text[:200]}...")
                        except Exception as e:
                            print(f"  ❌ POST {endpoint}: Error - {e}")
                            
                else:
                    print("❌ Authentication failed")
            else:
                print(f"❌ Authentication request failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(explore_api())