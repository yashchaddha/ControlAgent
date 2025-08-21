#!/usr/bin/env python3
"""
Test script to verify that only vector search results are displayed.
This tests the filtered response generation to ensure existing controls and ISO guidance are not shown.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from openai_service import openai_service
from rag_service import rag_service

async def test_vector_only_display():
    """Test that only vector search results are displayed"""
    
    print("🔍 Testing Vector-Only Display")
    print("=" * 50)
    
    # Test query
    test_query = "Show me the controls related to supply chain"
    test_user_id = "test_user"
    
    print(f"📝 Test Query: {test_query}")
    print(f"👤 Test User ID: {test_user_id}")
    print()
    
    try:
        # Step 1: Generate embedding for the query
        print("🔧 Step 1: Generating query embedding...")
        query_embedding = openai_service.get_embedding(test_query)
        print(f"   ✅ Embedding generated: {len(query_embedding)} dimensions")
        print()
        
        # Step 2: Test the enhanced general query context with vector_only=True
        print("🔍 Step 2: Testing enhanced general query context (vector_only=True)...")
        context = rag_service._get_general_query_context(
            query_embedding, 
            test_user_id, 
            test_query,
            vector_only=True
        )
        
        print(f"   📊 Context retrieved successfully")
        print(f"   📋 Context keys: {list(context.keys())}")
        print(f"   🎯 Vector only mode: {context.get('vector_only_mode', False)}")
        print(f"   🧮 Vector search count: {context.get('vector_search_count', 0)}")
        print()
        
        # Step 3: Analyze the results
        print("📊 Step 3: Analyzing search results...")
        
        total_controls = context.get("total_controls_found", 0)
        existing_controls = context.get("existing_controls", [])
        text_search_controls = context.get("text_search_controls", [])
        vector_controls = context.get("similar_controls", [])
        iso_guidance = context.get("iso_guidance", [])
        
        print(f"   📈 Total controls found: {total_controls}")
        print(f"   🏠 Existing user controls: {len(existing_controls)}")
        print(f"   🔤 Text search controls: {len(text_search_controls)}")
        print(f"   🧮 Vector search controls: {len(vector_controls)}")
        print(f"   📋 ISO guidance controls: {len(iso_guidance)}")
        print()
        
        # Step 4: Test the filtered response generation
        print("🎯 Step 4: Testing Vector-Only Response Generation...")
        
        if total_controls > 0:
            print("   📝 Generating vector-only response...")
            
            # Test the enhanced general controls response
            response = openai_service.generate_general_controls_response(
                test_query, 
                context, 
                {"organization_name": "Test Org", "domain": "Technology"}
            )
            
            print("   ✅ Response generated successfully")
            print("   📝 Response Preview:")
            print("   " + "-" * 50)
            
            # Show first few lines of response
            lines = response.split('\n')
            for i, line in enumerate(lines[:25]):  # Show first 25 lines
                print(f"   {line}")
            
            if len(lines) > 25:
                print(f"   ... and {len(lines) - 25} more lines")
            
            print("   " + "-" * 50)
            
            # Check if response contains only vector search results
            print("\n   🔍 Analyzing response content...")
            
            if "Vector Search" in response:
                print("   ✅ Response header correctly indicates Vector Search")
            else:
                print("   ⚠️  Response header doesn't indicate Vector Search")
            
            if "existing controls" not in response.lower() and "existing user controls" not in response.lower():
                print("   ✅ Response doesn't mention existing controls")
            else:
                print("   ❌ Response still mentions existing controls")
            
            if "iso 27001" not in response.lower() and "annex a" not in response.lower():
                print("   ✅ Response doesn't mention ISO 27001 or Annex A controls")
            else:
                print("   ❌ Response still mentions ISO 27001 or Annex A controls")
            
            if "relevance score" in response.lower() or "similarity" in response.lower():
                print("   ✅ Response includes relevance/similarity scores")
            else:
                print("   ⚠️  Response doesn't include relevance/similarity scores")
            
        else:
            print("   ⚠️  No controls found, skipping response generation")
        
        print()
        
        # Step 5: Test with vector_only=False for comparison
        print("🔄 Step 5: Testing with vector_only=False for comparison...")
        print("   🔍 This should return all control sources...")
        
        context_all = rag_service._get_general_query_context(
            query_embedding, 
            test_user_id, 
            test_query,
            vector_only=False
        )
        
        print(f"   📊 All sources context:")
        print(f"      Total controls: {context_all.get('total_controls_found', 0)}")
        print(f"      Vector only mode: {context_all.get('vector_only_mode', False)}")
        
        print()
        print("🎯 Vector-Only Display Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    await test_vector_only_display()

if __name__ == "__main__":
    asyncio.run(main())
