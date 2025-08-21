#!/usr/bin/env python3
"""
Test script to verify business continuity search functionality
"""

import asyncio
import sys
import os

async def test_business_continuity_search():
    """Test business continuity search functionality"""
    print("🧪 Testing Business Continuity Search")
    print("=" * 50)
    
    try:
        # Add app to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        # Test annex service
        print("🔧 Testing Annex Service...")
        from annex_service import AnnexService
        annex_service = AnnexService()
        print("   ✅ Annex service imported successfully")
        
        # Test business continuity search
        print(f"\n🔍 Testing business continuity search...")
        query = "show me the controls related to business continuity"
        
        # Search annex controls by text
        annex_results = annex_service.search_annex_controls(query, limit=10)
        print(f"   📋 Annex search results: {len(annex_results)} controls")
        
        if annex_results:
            print("   📝 Top annex controls:")
            for i, control in enumerate(annex_results[:3]):
                print(f"      {control.get('reference')}: {control.get('description')}")
                print(f"         Guidance: {control.get('guidance')[:80]}...")
        else:
            print("   ⚠️  No annex controls found for business continuity")
        
        # Test RAG service
        print(f"\n🔗 Testing RAG service...")
        from rag_service import RAGService
        rag_service = RAGService()
        print("   ✅ RAG service imported successfully")
        
        # Test context retrieval
        test_user_context = {
            "organization_name": "Test Corp",
            "domain": "Technology",
            "location": "Global"
        }
        
        print(f"   📝 Testing context retrieval for: '{query}'")
        
        # Get query embedding
        from openai_service import openai_service
        query_embedding = openai_service.get_embedding(query)
        
        # Get general query context
        context = rag_service._get_general_query_context(query_embedding, "test_user", query)
        
        print(f"      Similar controls: {len(context.get('similar_controls', []))}")
        print(f"      Similar risks: {len(context.get('similar_risks', []))}")
        print(f"      ISO guidance: {len(context.get('iso_guidance', []))}")
        print(f"      Existing controls: {len(context.get('existing_controls', []))}")
        
        if context.get('iso_guidance'):
            print(f"      Annex controls found:")
            for guidance in context['iso_guidance'][:3]:
                print(f"         {guidance.get('reference')}: {guidance.get('description')}")
        
        # Test response generation
        print(f"\n📝 Testing response generation...")
        from openai_service import OpenAIService
        openai_service = OpenAIService()
        
        response = openai_service.generate_show_controls_response(query, context, test_user_context)
        print(f"   ✅ Response generated successfully")
        print(f"   📊 Response length: {len(response)} characters")
        print(f"   📝 Response preview: {response[:200]}...")
        
        print("\n✅ Business continuity search test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_business_continuity_search())
