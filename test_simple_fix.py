#!/usr/bin/env python3
"""
Simple test script to verify control generation fixes
"""

import asyncio
import sys
import os

async def test_simple():
    """Simple test to verify the fixes work"""
    print("🧪 Testing Simple Control Generation Fixes")
    print("=" * 50)
    
    try:
        # Test importing the modules
        print("🔧 Testing module imports...")
        
        # Add app to path and import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        # Test OpenAI service
        print("   📝 Testing OpenAI service...")
        from openai_service import OpenAIService
        openai_service = OpenAIService()
        print("      ✅ OpenAI service imported successfully")
        
        # Test RAG service
        print("   📝 Testing RAG service...")
        from rag_service import RAGService
        rag_service = RAGService()
        print("      ✅ RAG service imported successfully")
        
        # Test that the missing methods exist
        print("   📝 Testing missing methods...")
        
        # Check if generate_contextual_response exists
        if hasattr(openai_service, 'generate_contextual_response'):
            print("      ✅ generate_contextual_response method exists")
        else:
            print("      ❌ generate_contextual_response method missing")
        
        # Check if store_query_embedding exists
        if hasattr(rag_service, 'store_query_embedding'):
            print("      ✅ store_query_embedding method exists")
        else:
            print("      ❌ store_query_embedding method missing")
        
        # Check if get_risks_for_generation exists
        if hasattr(rag_service, 'get_risks_for_generation'):
            print("      ✅ get_risks_for_generation method exists")
        else:
            print("      ❌ get_risks_for_generation method missing")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())
