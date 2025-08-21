#!/usr/bin/env python3
"""
Test script to verify Information Security control search is working properly.
This script tests the enhanced search functionality that combines:
1. Vector search on control embeddings
2. Text search on existing controls in MongoDB
3. ISO guidance from annex service
4. Existing user controls
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from rag_service import rag_service
from openai_service import openai_service
from database import mongodb

async def test_information_security_search():
    """Test the enhanced Information Security control search"""
    
    print("🔍 Testing Enhanced Information Security Control Search")
    print("=" * 60)
    
    # Test query
    test_query = "Show me the controls related to Information Security"
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

async def test_text_search_functionality():
    """Test the new text search functionality"""
    
    print("\n🔤 Testing Text Search Functionality")
    print("=" * 40)
    
    test_user_id = "test_user"
    test_query = "Information Security"
    
    try:
        print(f"🔍 Testing text search for: '{test_query}'")
        
        # Test the new MongoDB text search method
        text_results = mongodb.search_controls_by_text(test_query, test_user_id, limit=10)
        print(f"   📋 Text search found {len(text_results)} controls")
        
        if text_results:
            print("   📝 Text search results:")
            for i, control in enumerate(text_results[:3]):
                print(f"      {i+1}. {control.get('title', 'No Title')}")
                print(f"         Description: {control.get('description', 'No description')[:100]}...")
        else:
            print("   ⚠️  No text search results found")
            
    except Exception as e:
        print(f"❌ Text search test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Information Security Search Tests")
    print("=" * 60)
    
    # Test 1: Enhanced search functionality
    await test_information_security_search()
    
    # Test 2: Text search functionality
    await test_text_search_functionality()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
