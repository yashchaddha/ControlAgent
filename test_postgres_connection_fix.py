#!/usr/bin/env python3
"""
Test script to verify the PostgreSQL connection management fixes.
"""

import asyncio
import sys
import os
import time

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from postgres import postgres_service

async def test_connection_management():
    """Test the connection management functionality"""
    
    print("🔌 Testing PostgreSQL Connection Management")
    print("=" * 55)
    
    try:
        # Test 1: Initial connection status
        print("\n📊 Test 1: Initial Connection Status")
        print("-" * 35)
        status = postgres_service.get_connection_status()
        print(f"   Connection status: {status}")
        
        # Test 2: Health check
        print("\n🏥 Test 2: Database Health Check")
        print("-" * 35)
        health_ok = postgres_service.health_check()
        print(f"   Health check result: {'✅ PASSED' if health_ok else '❌ FAILED'}")
        
        # Test 3: Connection validation
        print("\n🔍 Test 3: Connection Validation")
        print("-" * 35)
        connection_valid = postgres_service.ensure_connection()
        print(f"   Connection validation: {'✅ PASSED' if connection_valid else '❌ FAILED'}")
        
        # Test 4: Simulate connection issues
        print("\n🧪 Test 4: Simulate Connection Issues")
        print("-" * 35)
        
        # Force close connection to simulate failure
        if postgres_service.conn:
            print("   🔄 Simulating connection failure...")
            postgres_service.conn.close()
            print("   ✅ Connection manually closed")
        
        # Test reconnection
        print("   🔄 Testing reconnection...")
        reconnected = postgres_service.ensure_connection()
        print(f"   Reconnection result: {'✅ PASSED' if reconnected else '❌ FAILED'}")
        
        # Test 5: Vector search after reconnection
        print("\n🔍 Test 5: Vector Search After Reconnection")
        print("-" * 40)
        
        if reconnected:
            # Create a dummy embedding for testing
            dummy_embedding = [0.1] * 1536  # 1536-dimensional vector
            
            print("   🔍 Testing control search...")
            controls = postgres_service.search_similar_controls(dummy_embedding, limit=5)
            print(f"   Controls found: {len(controls)}")
            
            print("   🔍 Testing risk search...")
            risks = postgres_service.search_similar_risks(dummy_embedding, limit=5)
            print(f"   Risks found: {len(risks)}")
            
            print("   ✅ Vector search tests completed")
        else:
            print("   ❌ Cannot test vector search: reconnection failed")
        
        # Test 6: Final health check
        print("\n🏥 Test 6: Final Health Check")
        print("-" * 35)
        final_health = postgres_service.health_check()
        print(f"   Final health check: {'✅ PASSED' if final_health else '❌ FAILED'}")
        
        # Test 7: Connection status after all tests
        print("\n📊 Test 7: Final Connection Status")
        print("-" * 35)
        final_status = postgres_service.get_connection_status()
        print(f"   Final connection status: {final_status}")
        
    except Exception as e:
        print(f"   ❌ Error during testing: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

async def test_connection_stability():
    """Test connection stability under repeated operations"""
    
    print("\n🔄 Testing Connection Stability")
    print("=" * 35)
    
    try:
        # Perform multiple operations to test stability
        dummy_embedding = [0.1] * 1536
        
        for i in range(5):
            print(f"   🔄 Iteration {i+1}/5")
            
            # Ensure connection
            if not postgres_service.ensure_connection():
                print(f"      ❌ Connection failed on iteration {i+1}")
                break
            
            # Perform searches
            try:
                controls = postgres_service.search_similar_controls(dummy_embedding, limit=2)
                risks = postgres_service.search_similar_risks(dummy_embedding, limit=2)
                print(f"      ✅ Searches completed successfully")
            except Exception as e:
                print(f"      ❌ Search failed: {e}")
                break
            
            # Brief delay
            await asyncio.sleep(0.1)
        
        print("   ✅ Connection stability test completed")
        
    except Exception as e:
        print(f"   ❌ Error during stability test: {e}")

async def test_error_recovery():
    """Test error recovery mechanisms"""
    
    print("\n🛠️  Testing Error Recovery")
    print("=" * 30)
    
    try:
        # Test 1: Force connection failure
        print("   🔄 Testing connection failure recovery...")
        
        if postgres_service.conn:
            postgres_service.conn.close()
            print("      ✅ Connection manually closed")
        
        # Test 2: Attempt operation (should trigger reconnection)
        print("   🔍 Attempting vector search (should trigger reconnection)...")
        dummy_embedding = [0.1] * 1536
        
        controls = postgres_service.search_similar_controls(dummy_embedding, limit=2)
        print(f"      ✅ Search completed after reconnection, found {len(controls)} controls")
        
        # Test 3: Verify connection is working
        print("   🔍 Verifying connection is working...")
        status = postgres_service.get_connection_status()
        print(f"      Connection status: {status}")
        
        print("   ✅ Error recovery test completed")
        
    except Exception as e:
        print(f"   ❌ Error during recovery test: {e}")

async def main():
    """Main test function"""
    await test_connection_management()
    await test_connection_stability()
    await test_error_recovery()
    
    print("\n🎯 PostgreSQL Connection Management Tests Completed!")
    print("=" * 55)

if __name__ == "__main__":
    asyncio.run(main())
