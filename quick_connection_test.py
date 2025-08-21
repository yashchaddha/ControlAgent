#!/usr/bin/env python3
"""
Quick test script to verify PostgreSQL connection fix.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_connection():
    """Quick test of the connection fix"""
    
    print("🔌 Quick PostgreSQL Connection Test")
    print("=" * 40)
    
    try:
        from postgres import postgres_service
        
        # Test 1: Check connection status
        print("\n📊 Connection Status:")
        status = postgres_service.get_connection_status()
        print(f"   {status}")
        
        # Test 2: Health check
        print("\n🏥 Health Check:")
        health_ok = postgres_service.health_check()
        print(f"   {'✅ PASSED' if health_ok else '❌ FAILED'}")
        
        # Test 3: Try a vector search
        print("\n🔍 Vector Search Test:")
        if health_ok:
            # Create dummy embedding
            dummy_embedding = [0.1] * 1536
            
            try:
                controls = postgres_service.search_similar_controls(dummy_embedding, limit=2)
                print(f"   ✅ Search successful, found {len(controls)} controls")
                
                risks = postgres_service.search_similar_risks(dummy_embedding, limit=2)
                print(f"   ✅ Risk search successful, found {len(risks)} risks")
                
            except Exception as e:
                print(f"   ❌ Search failed: {e}")
                return False
        else:
            print("   ❌ Health check failed, skipping search test")
            return False
        
        print("\n✅ All tests passed! Connection fix is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
