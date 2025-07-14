#!/usr/bin/env python3
"""
Test script to check the real TOP-EX API endpoints for shipping cost calculation.
Based on the documentation: https://documenter.getpostman.com/view/22619908/2sAYdfqWiw
"""
import asyncio
import aiohttp
import json
import urllib.parse
from config import Config

async def test_real_api():
    """Test the real TOP-EX API endpoints."""
    config = Config()
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Authenticate with the real API
        auth_url = "https://lk.top-ex.ru/api/auth"
        params = {
            'email': config.topex_email,
            'password': config.topex_password
        }
        
        print("🔑 Authenticating with TOP-EX API...")
        print(f"URL: {auth_url}")
        print(f"Email: {config.topex_email}")
        
        async with session.get(auth_url, params=params) as response:
            print(f"Auth Status: {response.status}")
            
            if response.status == 200:
                auth_data = await response.json()
                print(f"Auth Response: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")
                
                if auth_data.get('status'):
                    auth_token = auth_data.get('authToken')
                    print(f"✅ Authentication successful!")
                    print(f"Token: {auth_token[:20]}...")
                    
                    # Step 2: Test address book to get city codes
                    print("\n📖 Testing address book...")
                    address_url = "https://lk.top-ex.ru/api/addressBook/list"
                    address_params = {
                        'authToken': auth_token,
                        'type': 'express'
                    }
                    
                    async with session.get(address_url, params=address_params) as addr_response:
                        print(f"Address Book Status: {addr_response.status}")
                        
                        if addr_response.status == 200:
                            addr_data = await addr_response.json()
                            print(f"Address Book Response: {json.dumps(addr_data, indent=2, ensure_ascii=False)}")
                            
                            if addr_data.get('status') and addr_data.get('items'):
                                print(f"✅ Found {len(addr_data['items'])} address book entries")
                                
                                # Get some city codes for testing
                                city_codes = []
                                for item in addr_data['items'][:3]:  # Take first 3 items
                                    city_code = item.get('city')
                                    if city_code:
                                        city_codes.append(city_code)
                                
                                print(f"Found city codes: {city_codes}")
                                
                                # Step 3: Try to find delivery cost calculation endpoints
                                print("\n💰 Testing delivery cost calculation endpoints...")
                                
                                # Test various endpoints that might exist for calculation
                                test_endpoints = [
                                    "/express/calculate",
                                    "/express/cost",
                                    "/express/price",
                                    "/express/delivery/cost",
                                    "/delivery/calculate",
                                    "/calculate",
                                    "/cost",
                                    "/price"
                                ]
                                
                                for endpoint in test_endpoints:
                                    test_url = f"https://lk.top-ex.ru/api{endpoint}"
                                    test_params = {
                                        'authToken': auth_token,
                                        'from': city_codes[0] if len(city_codes) > 0 else 'cf862f89-442d-11dc-9497-0015170f8c09',
                                        'to': city_codes[1] if len(city_codes) > 1 else 'cf862f6c-442d-11dc-9497-0015170f8c09',
                                        'weight': 500
                                    }
                                    
                                    print(f"\n🔍 Testing: {endpoint}")
                                    try:
                                        async with session.get(test_url, params=test_params, timeout=10) as test_response:
                                            print(f"  Status: {test_response.status}")
                                            
                                            if test_response.status == 200:
                                                test_data = await test_response.json()
                                                print(f"  ✅ SUCCESS: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
                                                return  # Found working endpoint
                                            elif test_response.status == 404:
                                                print(f"  ❌ Not found (404)")
                                            else:
                                                text = await test_response.text()
                                                print(f"  ⚠️  Status {test_response.status}: {text[:100]}...")
                                    except Exception as e:
                                        print(f"  ❌ Error: {e}")
                                
                                print("\n🔍 No standard calculation endpoints found. The API might use a different structure.")
                                print("Need to check the full documentation or contact support for the correct endpoint.")
                                
                            else:
                                print(f"❌ Address book error: {addr_data.get('error', 'Unknown error')}")
                        else:
                            print(f"❌ Address book request failed: {addr_response.status}")
                    
                else:
                    print(f"❌ Authentication failed: {auth_data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Authentication request failed: {response.status}")
                text = await response.text()
                print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test_real_api())