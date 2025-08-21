#!/usr/bin/env python3
"""
Test script to verify annex-specific search functionality
"""

import asyncio
import sys
import os

async def test_annex_search():
    """Test annex-specific search functionality"""
    print("🧪 Testing Annex-Specific Search")
    print("=" * 50)
    
    try:
        # Add app to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        # Test annex service
        print("🔧 Testing Annex Service...")
        from annex_service import AnnexService
        annex_service = AnnexService()
        print("   ✅ Annex service imported successfully")
        
        # Test specific annex reference
        test_annex = "A.5.3"
        print(f"\n🔍 Testing annex reference: {test_annex}")
        
        # Get specific annex guidance
        annex_guidance = annex_service.get_annex_by_reference(test_annex)
        print(f"   📋 Annex guidance found: {annex_guidance.get('reference', 'None')}")
        if annex_guidance:
            print(f"   📝 Description: {annex_guidance.get('description', 'No description')}")
            print(f"   📝 Guidance: {annex_guidance.get('guidance', 'No guidance')}")
        
        # Get annex family controls
        annex_family = test_annex.split('.')[0] + '.' + test_annex.split('.')[1]
        print(f"\n🔍 Testing annex family: {annex_family}")
        
        if annex_family == "A.5":
            family_controls = annex_service.get_controls_by_domain("Organizational Controls")
        elif annex_family == "A.6":
            family_controls = annex_service.get_controls_by_domain("People Controls")
        elif annex_family == "A.7":
            family_controls = annex_service.get_controls_by_domain("Physical Controls")
        elif annex_family == "A.8":
            family_controls = annex_service.get_controls_by_domain("Technological Controls")
        else:
            family_controls = []
        
        print(f"   📋 Family controls found: {len(family_controls)}")
        if family_controls:
            print("   📝 Sample controls:")
            for control in family_controls[:3]:
                print(f"      {control.get('reference', 'Unknown')}: {control.get('description', 'Unknown')}")
        
        # Test RAG service
        print(f"\n🔗 Testing RAG service...")
        from rag_service import RAGService
        rag_service = RAGService()
        print("   ✅ RAG service imported successfully")
        
        # Test annex-specific context retrieval
        print(f"   📝 Testing annex-specific context retrieval for: {test_annex}")
        context = rag_service._get_controls_by_annex(test_annex, "test_user")
        
        print(f"      Controls found: {len(context.get('controls', []))}")
        print(f"      Annex guidance: {context.get('annex_guidance', {}).get('reference', 'None')}")
        print(f"      Annex family controls: {len(context.get('annex_family_controls', []))}")
        print(f"      Sources: {context.get('sources', {})}")
        
        if context.get('controls'):
            print(f"      Sample controls:")
            for i, control in enumerate(context['controls'][:3]):
                print(f"         {i+1}. {control.get('control_id', 'Unknown')} - {control.get('title', 'No title')}")
                print(f"            Annex: {control.get('annex_reference', 'Unknown')}")
                print(f"            Source: {control.get('source', 'Unknown')}")
        
        # Test response generation
        print(f"\n📝 Testing response generation...")
        from openai_service import OpenAIService
        openai_service = OpenAIService()
        
        test_query = f"show controls related to {test_annex}"
        test_user_context = {
            "organization_name": "Test Corp",
            "domain": "Technology",
            "location": "Global"
        }
        
        response = openai_service.generate_show_controls_response(test_query, context, test_user_context)
        print(f"   ✅ Response generated successfully")
        print(f"   📊 Response length: {len(response)} characters")
        print(f"   📝 Response preview: {response[:300]}...")
        
        print("\n✅ Annex-specific search test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_annex_search())
