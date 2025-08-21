#!/usr/bin/env python3
"""
Comprehensive test script to verify the full workflow for supply chain control search.
This tests the entire pipeline from intent classification to response generation.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from openai_service import openai_service
from rag_service import rag_service
from langgraph_agent import iso_agent

async def test_supply_chain_full_workflow():
    """Test the complete workflow for supply chain control search"""
    
    print("🚀 Testing Complete Supply Chain Control Search Workflow")
    print("=" * 70)
    
    # Test query
    test_query = "Show me the controls related to supply chain"
    test_user_id = "test_user"
    
    print(f"📝 Test Query: {test_query}")
    print(f"👤 Test User ID: {test_user_id}")
    print()
    
    try:
        # Step 1: Test Intent Classification
        print("🔧 Step 1: Testing Intent Classification")
        print("-" * 40)
        
        user_context = {"organization_name": "Test Org", "domain": "Technology"}
        intent_result = openai_service.classify_intent(test_query, user_context)
        
        print(f"   🎯 Intent: {intent_result.get('intent', 'Unknown')}")
        print(f"   📋 Parameters: {intent_result.get('parameters', {})}")
        
        # Check if intent is correct
        if intent_result.get('intent') == 'query_controls':
            print("   ✅ CORRECT: Intent classified as query_controls")
        else:
            print(f"   ⚠️  WARNING: Intent classified as {intent_result.get('intent')}")
            print("      This might cause issues in the workflow")
        
        print()
        
        # Step 2: Test Context Retrieval
        print("🔍 Step 2: Testing Context Retrieval")
        print("-" * 40)
        
        # Generate embedding for the query
        query_embedding = openai_service.get_embedding(test_query)
        print(f"   ✅ Query embedding generated: {len(query_embedding)} dimensions")
        
        # Test the enhanced general query context
        context = rag_service._get_general_query_context(
            query_embedding, 
            test_user_id, 
            test_query
        )
        
        print(f"   📊 Context retrieved successfully")
        print(f"   📋 Context keys: {list(context.keys())}")
        
        # Analyze the results
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
        
        if total_controls > 0:
            print("   ✅ SUCCESS: Controls found through enhanced search")
        else:
            print("   ⚠️  WARNING: No controls found - this might indicate an issue")
        
        print()
        
        # Step 3: Test Response Generation
        print("🎯 Step 3: Testing Response Generation")
        print("-" * 40)
        
        if total_controls > 0:
            print("   📝 Generating enhanced response...")
            
            # Test the enhanced general controls response
            response = openai_service.generate_general_controls_response(
                test_query, 
                context, 
                user_context
            )
            
            print("   ✅ Response generated successfully")
            print("   📝 Response Preview:")
            print("   " + "-" * 50)
            
            # Show first few lines of response
            lines = response.split('\n')
            for i, line in enumerate(lines[:20]):  # Show first 20 lines
                print(f"   {line}")
            
            if len(lines) > 20:
                print(f"   ... and {len(lines) - 20} more lines")
            
            print("   " + "-" * 50)
            
        else:
            print("   ⚠️  Skipping response generation - no controls found")
        
        print()
        
        # Step 4: Test Fallback Category Search (if intent was misclassified)
        print("🔄 Step 4: Testing Fallback Category Search")
        print("-" * 40)
        
        print("   🔍 Testing what happens if intent was misclassified as show_controls_by_category")
        
        # Simulate the category search that would happen if intent was misclassified
        category_context = rag_service._get_controls_by_category("supply chain", test_user_id)
        
        print(f"   📊 Category search results:")
        print(f"      Total controls: {category_context.get('total_controls_found', 0)}")
        print(f"      Existing controls: {len(category_context.get('existing_controls', []))}")
        print(f"      Text search controls: {len(category_context.get('text_search_controls', []))}")
        print(f"      Vector controls: {len(category_context.get('vector_controls', []))}")
        print(f"      ISO guidance: {len(category_context.get('iso_guidance', []))}")
        
        if category_context.get('total_controls_found', 0) > 0:
            print("   ✅ SUCCESS: Fallback category search found controls")
        else:
            print("   ⚠️  WARNING: Fallback category search also found no controls")
        
        print()
        
        # Step 5: Summary and Recommendations
        print("📊 Step 5: Summary and Recommendations")
        print("-" * 40)
        
        print("   🎯 Workflow Analysis:")
        
        if intent_result.get('intent') == 'query_controls' and total_controls > 0:
            print("      ✅ PRIMARY PATH: Intent classification correct, controls found")
            print("      ✅ User will get comprehensive supply chain controls")
        elif intent_result.get('intent') == 'show_controls_by_category' and category_context.get('total_controls_found', 0) > 0:
            print("      ✅ FALLBACK PATH: Intent misclassified but fallback search successful")
            print("      ✅ User will still get supply chain controls")
        else:
            print("      ❌ ISSUE: Neither primary nor fallback path found controls")
            print("      ❌ User will get 'no controls found' response")
        
        print()
        print("   🔧 Recommendations:")
        
        if intent_result.get('intent') != 'query_controls':
            print("      - Fix intent classification to properly identify supply chain queries")
        
        if total_controls == 0 and category_context.get('total_controls_found', 0) == 0:
            print("      - Check if supply chain controls exist in the database")
            print("      - Verify vector embeddings are properly stored")
            print("      - Ensure text search is working correctly")
        
        print()
        print("🎯 Full Workflow Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    await test_supply_chain_full_workflow()

if __name__ == "__main__":
    asyncio.run(main())
