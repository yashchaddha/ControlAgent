#!/usr/bin/env python3
"""
Test script to verify Supply Chain control search is working properly.
This script tests the enhanced search functionality for supply chain related queries.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from rag_service import rag_service
from openai_service import openai_service
from database import mongodb

async def test_supply_chain_search():
    """Test the enhanced Supply Chain control search"""
    
    print("🔍 Testing Enhanced Supply Chain Control Search")
    print("=" * 60)
    
    # Test query
    test_query = "Show me the controls related to supply chain"
    test_user_id = "test_user"  # Use a test user ID
    
    print(f"📝 Test Query: {test_query}")
    print(f"👤 Test User ID: {test_user_id}")
    print()
    
    try:
        # Step 1: Generate embedding for the query
        print("🔧 Step 1: Generating query embedding...")
        query_embedding = openai_service.get_embedding(test_query)
        print(f"   ✅ Embedding generated: {len(query_embedding)} dimensions")
        print()
        
        # Step 2: Test the enhanced general query context
        print("🔍 Step 2: Testing enhanced general query context...")
        context = rag_service._get_general_query_context(
            query_embedding, 
            test_user_id, 
            test_query
        )
        
        print(f"   📊 Context retrieved successfully")
        print(f"   📋 Context keys: {list(context.keys())}")
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
        
        # Step 4: Test the enhanced response generation
        print("🎯 Step 4: Testing enhanced response generation...")
        
        # Check if we have any controls to work with
        if total_controls > 0:
            print("   ✅ Controls found, testing response generation...")
            
            # Test the enhanced general controls response
            response = openai_service.generate_general_controls_response(
                test_query, 
                context, 
                {"organization_name": "Test Org", "domain": "Technology"}
            )
            
            print("   📝 Generated Response:")
            print("   " + "-" * 40)
            print(response)
            print("   " + "-" * 40)
            
        else:
            print("   ⚠️  No controls found, checking why...")
            
            # Check if there are any controls in the database
            try:
                all_controls = list(mongodb.controls.find({"user_id": test_user_id}))
                print(f"   📋 Total controls in database for user: {len(all_controls)}")
                
                if all_controls:
                    print("   📝 Sample control titles:")
                    for i, control in enumerate(all_controls[:3]):
                        print(f"      {i+1}. {control.get('title', 'No Title')}")
                else:
                    print("   ❌ No controls found in database for this user")
                    
            except Exception as e:
                print(f"   ❌ Error checking database: {e}")
        
        print()
        print("🎯 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_supply_chain_text_search():
    """Test the text search functionality for supply chain controls"""
    
    print("\n🔤 Testing Supply Chain Text Search Functionality")
    print("=" * 50)
    
    test_user_id = "test_user"
    test_queries = [
        "supply chain",
        "supply chain risk", 
        "vendor",
        "third party",
        "outsourcing"
    ]
    
    for query in test_queries:
        try:
            print(f"🔍 Testing text search for: '{query}'")
            
            # Test the MongoDB text search method
            text_results = mongodb.search_controls_by_text(query, test_user_id, limit=10)
            print(f"   📋 Text search found {len(text_results)} controls")
            
            if text_results:
                print("   📝 Text search results:")
                for i, control in enumerate(text_results[:3]):
                    print(f"      {i+1}. {control.get('title', 'No Title')}")
                    print(f"         Description: {control.get('description', 'No description')[:100]}...")
            else:
                print("   ⚠️  No text search results found")
                
        except Exception as e:
            print(f"❌ Text search test failed for '{query}': {e}")
        
        print()

async def test_annex_service_supply_chain():
    """Test the annex service for supply chain related controls"""
    
    print("\n📋 Testing Annex Service Supply Chain Search")
    print("=" * 50)
    
    test_queries = [
        "supply chain",
        "vendor management",
        "third party risk",
        "outsourcing"
    ]
    
    try:
        from annex_service import annex_service
        
        for query in test_queries:
            print(f"🔍 Testing annex search for: '{query}'")
            
            # Test the annex service search
            annex_results = annex_service.search_annex_controls(query, limit=5)
            print(f"   📋 Annex search found {len(annex_results)} controls")
            
            if annex_results:
                print("   📝 Annex search results:")
                for i, control in enumerate(annex_results[:3]):
                    print(f"      {i+1}. {control.get('reference', 'No Reference')}")
                    print(f"         Description: {control.get('description', 'No description')}")
            else:
                print("   ⚠️  No annex search results found")
                
            print()
            
    except Exception as e:
        print(f"❌ Annex service test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Supply Chain Control Search Tests")
    print("=" * 60)
    
    # Test 1: Enhanced search functionality for supply chain
    await test_supply_chain_search()
    
    # Test 2: Text search functionality for supply chain
    await test_supply_chain_text_search()
    
    # Test 3: Annex service for supply chain
    await test_annex_service_supply_chain()
    
    print("\n✅ All Supply Chain tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
