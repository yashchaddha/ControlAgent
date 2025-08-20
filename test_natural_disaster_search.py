#!/usr/bin/env python3
"""
Test script to debug natural disaster search specifically
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_natural_disaster_search():
    """Test natural disaster search specifically"""
    
    print("🔍 Testing Natural Disaster Search")
    print("=" * 40)
    
    try:
        from app.rag_service import rag_service
        
        print("✅ RAG service imported successfully")
        
        # Test the specific query that's failing
        test_query = "risks related to natural disasters"
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
            
            # Show what was actually found
            print(f"\n📋 What was found:")
            raw_results = debug_result['raw_results']
            print(f"   Risks: {len(raw_results.get('risks', []))}")
            print(f"   Controls: {len(raw_results.get('controls', []))}")
            print(f"   Guidance: {len(raw_results.get('guidance', []))}")
            
            if raw_results.get('risks'):
                print(f"\n   Top risk results:")
                for i, risk in enumerate(raw_results['risks'][:3]):
                    print(f"     {i+1}. Similarity: {risk.get('similarity', 0):.3f}")
                    print(f"        Description: {risk.get('description', 'Unknown')[:80]}...")
                    print(f"        Category: {risk.get('category', 'Unknown')}")
            
            # Show final context
            print(f"\n🎯 Final context retrieved:")
            final_context = debug_result['final_context']
            print(f"   Similar controls: {len(final_context.get('similar_controls', []))}")
            print(f"   Similar risks: {len(final_context.get('similar_risks', []))}")
            print(f"   ISO guidance: {len(final_context.get('iso_guidance', []))}")
            print(f"   User risks: {len(final_context.get('user_risks', []))}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_direct_vector_search():
    """Test direct vector search for natural disasters"""
    
    print("\n🔍 Testing Direct Vector Search")
    print("=" * 30)
    
    try:
        from app.postgres import postgres_service
        from app.openai_service import openai_service
        
        # Generate embedding for natural disasters
        test_query = "natural disasters"
        test_embedding = openai_service.get_embedding(test_query)
        print(f"✅ Query embedding generated: {len(test_embedding)} dimensions")
        
        # Test risk search directly
        print(f"\n📊 Testing risk search for '{test_query}':")
        risks = postgres_service.search_similar_risks(test_embedding, limit=10)
        print(f"   Found {len(risks)} risks")
        
        if risks:
            print("   Top results:")
            for i, risk in enumerate(risks[:3]):
                print(f"     {i+1}. Similarity: {risk.get('similarity', 0):.3f}")
                print(f"        Description: {risk.get('description', 'Unknown')[:80]}...")
                print(f"        Category: {risk.get('category', 'Unknown')}")
        else:
            print("   ❌ No risks found!")
        
        # Test with different variations
        variations = [
            "natural disasters",
            "natural disaster",
            "typhoons",
            "earthquakes",
            "floods",
            "disaster recovery"
        ]
        
        print(f"\n🔄 Testing variations:")
        for variation in variations:
            var_embedding = openai_service.get_embedding(variation)
            var_risks = postgres_service.search_similar_risks(var_embedding, limit=3)
            print(f"   '{variation}': {len(var_risks)} risks found")
            if var_risks:
                top_risk = var_risks[0]
                print(f"      Top similarity: {top_risk.get('similarity', 0):.3f}")
        
    except Exception as e:
        print(f"❌ Direct vector search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Natural Disaster Search Debug Test")
    print("This will help identify why natural disaster searches aren't working")
    print()
    
    # Test the RAG service
    test_natural_disaster_search()
    
    # Test direct vector search
    test_direct_vector_search()
    
    print("\n🎯 Debug test completed!")
