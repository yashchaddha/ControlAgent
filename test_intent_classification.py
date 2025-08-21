#!/usr/bin/env python3
"""
Test script to verify intent classification is working correctly for supply chain queries.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from openai_service import openai_service

async def test_intent_classification():
    """Test the intent classification for various queries"""
    
    print("🧠 Testing Intent Classification")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Show me the controls related to supply chain",
        "Show me the controls related to information security", 
        "Show me the controls related to cybersecurity",
        "Show me controls for operational risk",
        "Show me controls for financial risk",
        "Generate controls for supply chain risk",
        "What controls exist for data protection?",
        "Show me the controls related to vendor management"
    ]
    
    # Mock user context
    user_context = {
        "organization_name": "Test Organization",
        "domain": "Technology"
    }
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Test intent classification
            result = openai_service.classify_intent(query, user_context)
            
            print(f"   🎯 Intent: {result.get('intent', 'Unknown')}")
            print(f"   📋 Parameters: {result.get('parameters', {})}")
            
            # Analyze the result
            intent = result.get('intent', '')
            if intent == 'query_controls':
                print(f"   ✅ CORRECT: Classified as query_controls (general information request)")
            elif intent == 'show_controls_by_category':
                print(f"   ⚠️  POTENTIAL ISSUE: Classified as show_controls_by_category")
                print(f"      This should only be used for explicit risk category requests")
            elif intent.startswith('generate_controls'):
                print(f"   ✅ CORRECT: Classified as {intent} (control generation request)")
            else:
                print(f"   ℹ️  Classified as {intent}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Intent Classification Test Completed!")

async def main():
    """Main test function"""
    await test_intent_classification()

if __name__ == "__main__":
    asyncio.run(main())
