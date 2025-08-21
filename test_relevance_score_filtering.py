#!/usr/bin/env python3
"""
Test script to verify that the system only shows controls with relevance scores > 0.8.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from openai_service import openai_service
from rag_service import rag_service

async def test_relevance_score_filtering():
    """Test that only controls with relevance score > 0.8 are displayed"""
    
    print("🎯 Testing Relevance Score Filtering (> 0.8)")
    print("=" * 60)
    
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
            
            # Get context with increased vector search limit
            context = rag_service._get_general_query_context(
                query_embedding, 
                test_user_id, 
                test_query,
                vector_only=True
            )
            
            # Analyze the context
            print("   📊 Context Analysis:")
            print(f"      Total vector search controls: {context.get('vector_search_count', 0)}")
            print(f"      High-relevance controls (>0.8): {context.get('high_relevance_count', 0)}")
            print(f"      Total combined controls: {context.get('total_controls_found', 0)}")
            
            # Generate response
            response = openai_service.generate_general_controls_response(
                test_query, 
                context, 
                {"organization_name": "Test Org", "domain": "Technology"}
            )
            
            print("   📝 Response generated successfully")
            
            # Check if response mentions high relevance
            print("   🔍 Checking response content...")
            
            if "high relevance" in response.lower():
                print("   ✅ Response mentions high relevance filtering")
            else:
                print("   ⚠️  Response doesn't mention high relevance filtering")
            
            # Check if response mentions the 0.8 threshold
            if "0.8" in response or "0.80" in response:
                print("   ✅ Response mentions the 0.8 threshold")
            else:
                print("   ⚠️  Response doesn't mention the 0.8 threshold")
            
            # Count how many controls are actually shown
            control_count = response.count("### Control")
            print(f"   📊 Controls displayed in response: {control_count}")
            
            # Check if the number of displayed controls matches high-relevance count
            expected_count = context.get('high_relevance_count', 0)
            if control_count == expected_count:
                print(f"   ✅ Correct number of controls displayed ({control_count} = {expected_count})")
            else:
                print(f"   ⚠️  Mismatch: {control_count} controls displayed vs {expected_count} expected")
            
            # Show first few lines of response
            print("   📋 Response Preview:")
            lines = response.split('\n')
            for j, line in enumerate(lines[:20]):  # Show first 20 lines
                if line.strip():  # Only show non-empty lines
                    print(f"      {line}")
            
            if len(lines) > 20:
                print(f"      ... and {len(lines) - 20} more lines")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("🎯 Relevance Score Filtering Test Completed!")

async def test_threshold_behavior():
    """Test different threshold behaviors"""
    
    print("\n🧪 Testing Threshold Behavior")
    print("=" * 40)
    
    test_query = "Show me the controls related to supply chain"
    test_user_id = "test_user"
    
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
        
        print(f"🔍 Query: {test_query}")
        print(f"📊 Vector search results: {context.get('vector_search_count', 0)}")
        print(f"🎯 High-relevance results (>0.8): {context.get('high_relevance_count', 0)}")
        
        # Show some sample scores
        vector_controls = [c for c in context.get('similar_controls', []) if c.get('source') == 'vector_search']
        if vector_controls:
            print(f"📈 Sample relevance scores:")
            for i, control in enumerate(vector_controls[:5]):
                score = control.get('similarity', 0)
                title = control.get('title', 'No Title')[:50]
                print(f"   {i+1}. {title}... - Score: {score:.3f}")
        
        # Generate response
        response = openai_service.generate_general_controls_response(
            test_query, 
            context, 
            {"organization_name": "Test Org", "domain": "Technology"}
        )
        
        print(f"\n📝 Response generated with {response.count('### Control')} controls")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main test function"""
    await test_relevance_score_filtering()
    await test_threshold_behavior()

if __name__ == "__main__":
    asyncio.run(main())
