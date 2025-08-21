#!/usr/bin/env python3
"""
Test script to verify annex2.json integration
"""

import asyncio
import sys
import os

async def test_annex_integration():
    """Test that the annex service is properly integrated"""
    print("🧪 Testing Annex2.json Integration")
    print("=" * 50)
    
    try:
        # Add app to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        # Test annex service
        print("🔧 Testing Annex Service...")
        from annex_service import AnnexService
        annex_service = AnnexService()
        print("   ✅ Annex service imported successfully")
        
        # Test loading annex data
        print(f"\n📋 Annex data loaded: {len(annex_service.annex_data)} controls")
        
        if annex_service.annex_data:
            print("   📝 Sample controls:")
            for i, control in enumerate(annex_service.annex_data[:3]):
                print(f"      {control.get('reference', 'Unknown')}: {control.get('description', 'Unknown')}")
                print(f"         Guidance: {control.get('guidance', 'No guidance')[:80]}...")
        
        # Test category filtering
        print(f"\n🎯 Testing category filtering...")
        test_categories = ["Operational Risk", "Technical Risk", "Physical Risk", "Cybersecurity Risk"]
        
        for category in test_categories:
            controls = annex_service.get_annex_controls(category, limit=3)
            print(f"   {category}: {len(controls)} controls")
            if controls:
                print(f"      Examples: {[c.get('reference') for c in controls]}")
        
        # Test RAG service integration
        print(f"\n🔗 Testing RAG service integration...")
        from rag_service import RAGService
        rag_service = RAGService()
        print("   ✅ RAG service imported successfully")
        
        # Test context retrieval
        test_risk = {
            "description": "Supply chain disruption due to natural disasters",
            "category": "Supply Chain Risk",
            "impact": "High",
            "likelihood": "Medium"
        }
        
        test_user_context = {
            "organization_name": "Test Corp",
            "domain": "Technology",
            "location": "Global"
        }
        
        print(f"   📝 Testing context retrieval for: {test_risk['description'][:50]}...")
        context = rag_service.retrieve_context_for_control_generation(test_risk, test_user_context)
        
        print(f"      Similar risks: {len(context.get('similar_risks', []))}")
        print(f"      Similar controls: {len(context.get('similar_controls', []))}")
        print(f"      ISO guidance: {len(context.get('iso_guidance', []))}")
        
        if context.get('iso_guidance'):
            print(f"      Annex controls found:")
            for guidance in context['iso_guidance'][:3]:
                print(f"         {guidance.get('reference')}: {guidance.get('description')}")
        
        print("\n✅ Annex integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_annex_integration())
