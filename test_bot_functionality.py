#!/usr/bin/env python3
"""
Test script to verify the complete bot functionality.
"""
import asyncio
from excel_processor import ExcelProcessor
from topex_api import TopExAPI
from config import Config

async def main():
    print("🚀 Testing Telegram Bot Functionality")
    print("=" * 50)
    
    # Test 1: Excel file processing
    print("\n1️⃣ Testing Excel file processing...")
    try:
        processor = ExcelProcessor()
        routes = processor.process_file('attached_assets/routs_1752490515869.xlsx')
        print(f"✅ Successfully processed {len(routes)} routes:")
        for i, route in enumerate(routes, 1):
            print(f"   {i}. {route['origin']} → {route['destination']} ({route['weight']}g)")
    except Exception as e:
        print(f"❌ Excel processing failed: {e}")
        return
    
    # Test 2: TOP-EX API authentication
    print("\n2️⃣ Testing TOP-EX API integration...")
    try:
        config = Config()
        api = TopExAPI(config)
        
        # Test authentication
        auth_result = await api._authenticate()
        if auth_result:
            print("✅ TOP-EX API authentication successful")
        else:
            print("❌ TOP-EX API authentication failed")
            return
        
        # Test shipping cost calculation for first route
        if routes:
            route = routes[0]
            print(f"   Testing route: {route['origin']} → {route['destination']} ({route['weight']}g)")
            
            costs = await api.calculate_shipping_cost(
                route['origin'], 
                route['destination'], 
                route['weight']
            )
            print(f"   Result: {costs}")
            
        await api.close()
        
    except Exception as e:
        print(f"❌ API integration failed: {e}")
        return
    
    # Test 3: Configuration
    print("\n3️⃣ Testing configuration...")
    try:
        config = Config()
        print(f"✅ Configuration loaded successfully")
        print(f"   API Base URL: {config.topex_api_base}")
        print(f"   Max file size: {config.max_file_size // (1024*1024)}MB")
        print(f"   Request timeout: {config.request_timeout}s")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\nBot is ready to use:")
    print("1. Send Excel files with shipping routes")
    print("2. Bot will process and calculate costs")
    print("3. Results will be returned in Telegram")

if __name__ == "__main__":
    asyncio.run(main())