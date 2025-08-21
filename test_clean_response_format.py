#!/usr/bin/env python3
"""
Test script to verify that the response format is clean without "Vector Search" terminology.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from openai_service import openai_service
from rag_service import rag_service

async def test_clean_response_format():
    """Test that the response format is clean without technical jargon"""
    
    print("🧹 Testing Clean Response Format")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Show me the controls related to supply chain",
        "Show me the controls related to information security",
        "What controls exist for cybersecurity?"
    ]
    
    test_user_id = "test_user"
    
    for i, test_query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test_query}")
        print("-" * 40)
        
        try:
            # Generate embedding for the query
            query_embedding = openai_service.get_embedding(test_query)
            
            # Get context
            context = rag_service._get_general_query_context(
                query_embedding, 
                test_user_id, 
                test_query,
                vector_only=True
            )
            
            # Generate response
            response = openai_service.generate_general_controls_response(
                test_query, 
                context, 
                {"organization_name": "Test Org", "domain": "Technology"}
            )
            
            print("   📝 Response generated successfully")
            
            # Check for unwanted terminology
            print("   🔍 Checking response content...")
            
            # Check that "Vector Search" terminology is NOT present
            if "vector search" not in response.lower() and "vector database" not in response.lower():
                print("   ✅ No 'Vector Search' terminology found")
            else:
                print("   ❌ 'Vector Search' terminology still present")
            
            # Check that the response is clean and direct
            if "## " in response and "### Control" in response:
                print("   ✅ Clean formatting with proper headers")
            else:
                print("   ❌ Response formatting issues")
            
            # Check that relevance scores are included
            if "relevance score" in response.lower():
                print("   ✅ Relevance scores included")
            else:
                print("   ⚠️  Relevance scores not found")
            
            # Show first few lines of response
            print("   📋 Response Preview:")
            lines = response.split('\n')
            for j, line in enumerate(lines[:15]):  # Show first 15 lines
                if line.strip():  # Only show non-empty lines
                    print(f"      {line}")
            
            if len(lines) > 15:
                print(f"      ... and {len(lines) - 15} more lines")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("🎯 Clean Response Format Test Completed!")

async def main():
    """Main test function"""
    await test_clean_response_format()

if __name__ == "__main__":
    asyncio.run(main())
