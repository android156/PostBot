#!/usr/bin/env python3
"""
Test script to verify complete workflow with real API documentation.
"""
import asyncio
from config import Config
from topex_api import TopExAPI
from excel_processor import ExcelProcessor

async def test_full_workflow():
    """Test the complete workflow with real API."""
    
    # Initialize components
    config = Config()
    api = TopExAPI(config)
    processor = ExcelProcessor()
    
    print("🧪 Testing complete workflow with real API documentation...")
    
    # Test 1: Process Excel file
    print("\n1️⃣ Testing Excel processing...")
    try:
        excel_data = processor.process_file("attached_assets/routs_1752490515869.xlsx")
        print(f"✅ Excel processed successfully: {len(excel_data)} routes found")
        
        # Show first few routes
        for i, route in enumerate(excel_data[:3]):
            print(f"   Route {i+1}: {route['origin']} → {route['destination']} ({route['weight']}g)")
            
    except Exception as e:
        print(f"❌ Excel processing failed: {e}")
        return
    
    # Test 2: API Authentication
    print("\n2️⃣ Testing API authentication...")
    try:
        await api._ensure_authenticated()
        print("✅ API authentication successful")
        print(f"   Token: {api.auth_token[:20]}...")
        
    except Exception as e:
        print(f"❌ API authentication failed: {e}")
        return
    
    # Test 3: Test shipping cost calculation for a few routes
    print("\n3️⃣ Testing shipping cost calculation...")
    
    test_routes = excel_data[:3]  # Test first 3 routes
    
    for i, route in enumerate(test_routes):
        print(f"\n   Route {i+1}: {route['origin']} → {route['destination']} ({route['weight']}g)")
        
        try:
            result = await api.calculate_shipping_cost(
                route['origin'], 
                route['destination'], 
                route['weight']
            )
            
            print(f"   📊 Result:")
            for key, value in result.items():
                print(f"     {key}: {value}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 4: Close resources
    print("\n4️⃣ Cleaning up...")
    await api.close()
    print("✅ Resources cleaned up")
    
    print("\n🎉 Full workflow test completed!")

if __name__ == "__main__":
    asyncio.run(test_full_workflow())