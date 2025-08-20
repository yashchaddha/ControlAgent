#!/usr/bin/env python3
"""
Test script to debug supply chain search issue
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_supply_chain_search():
    """Test supply chain search specifically"""
    
    print("🔍 Testing Supply Chain Search")
    print("=" * 40)
    
    try:
        # Import with absolute paths
        from app.rag_service import rag_service
        
        print("✅ RAG service imported successfully")
        
        # Test the specific query that's failing
        test_query = "supply chain"
        print(f"\n🔍 Testing query: '{test_query}'")
        
        # Use the debug method
        debug_result = rag_service.debug_query_search(test_query, "test_user")
        
        if "error" in debug_result:
            print(f"❌ Debug failed: {debug_result['error']}")
        else:
            print(f"\n✅ Debug completed successfully!")
            print(f"Total raw results found: {debug_result['debug_info']['total_raw_results']}")
            
            # Show threshold analysis
            print(f"\n📊 Threshold Analysis:")
            for threshold, count in debug_result['debug_info']['threshold_analysis'].items():
                print(f"   Threshold {threshold:.1f}: {count} results")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_variations():
    """Test different variations of supply chain queries"""
    
    print("\n🔄 Testing Query Variations")
    print("=" * 30)
    
    try:
        from app.rag_service import rag_service
        
        variations = [
            "supply chain",
            "supply chain security",
            "supplier relationships",
            "vendor management",
            "third party risk",
            "supply chain risk",
            "supplier security",
            "vendor security"
        ]
        
        for variation in variations:
            print(f"\n🔍 Testing: '{variation}'")
            debug_result = rag_service.debug_query_search(variation, "test_user")
            
            if "error" not in debug_result:
                total_results = debug_result['debug_info']['total_raw_results']
                print(f"   Results found: {total_results}")
                
                if total_results == 0:
                    print("   ❌ No results - this variation needs investigation")
                elif total_results < 3:
                    print("   ⚠️  Few results - consider lowering thresholds")
                else:
                    print("   ✅ Good number of results")
            else:
                print(f"   ❌ Failed: {debug_result['error']}")
        
    except Exception as e:
        print(f"❌ Variations test failed: {e}")

if __name__ == "__main__":
    print("🚀 Supply Chain Search Debug Test")
    print("This will help identify why supply chain searches aren't working")
    print()
    
    # Test the main query
    test_supply_chain_search()
    
    # Test variations
    test_variations()
    
    print("\n🎯 Debug test completed!")
    print("Check the output above to identify the issue.")
