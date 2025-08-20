#!/usr/bin/env python3
"""
Test script for enhanced vector search capabilities
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_vector_search():
    """Test the enhanced vector search functionality"""
    
    print("🧪 Testing Enhanced Vector Search Capabilities")
    print("=" * 50)
    
    try:
        # Import services
        from rag_service import rag_service
        from openai_service import openai_service
        from postgres import postgres_service
        
        print("✅ Services imported successfully")
        
        # Test 1: Generate embeddings for a sample query
        print("\n🔍 Test 1: Query Embedding Generation")
        sample_query = "How do I implement access control for cloud services?"
        print(f"Sample query: {sample_query}")
        
        embedding = openai_service.get_embedding(sample_query)
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
        
        # Test 2: Vector search capabilities
        print("\n🔍 Test 2: Vector Search")
        
        # Check database statistics
        stats = postgres_service.get_search_statistics()
        print(f"📊 Vector Database Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test 3: Enhanced context retrieval
        print("\n🔍 Test 3: Enhanced Context Retrieval")
        
        # Simulate user context
        user_context = {
            "organization_name": "Test Corp",
            "domain": "Technology",
            "location": "San Francisco"
        }
        
        # Test context retrieval
        context = rag_service.retrieve_context_for_query(
            sample_query, 
            "query_controls", 
            {}, 
            "test_user"
        )
        
        print(f"✅ Context retrieved successfully")
        print(f"   Controls found: {len(context.get('similar_controls', []))}")
        print(f"   Risks found: {len(context.get('similar_risks', []))}")
        print(f"   Guidance found: {len(context.get('iso_guidance', []))}")
        print(f"   User risks found: {len(context.get('user_risks', []))}")
        
        # Test 4: Query embedding storage
        print("\n🔍 Test 4: Query Embedding Storage")
        
        # Store a test query embedding
        test_response_context = {
            "intent": "query_controls",
            "generated_controls_count": 0,
            "retrieved_context_summary": {
                "controls_found": len(context.get('similar_controls', [])),
                "risks_found": len(context.get('similar_risks', [])),
                "guidance_found": len(context.get('iso_guidance', []))
            }
        }
        
        rag_service.store_query_embedding(
            query=sample_query,
            user_id="test_user",
            intent="query_controls",
            response_context=test_response_context
        )
        print("✅ Query embedding stored successfully")
        
        # Test 5: Similar query search
        print("\n🔍 Test 5: Similar Query Search")
        
        similar_queries = postgres_service.search_similar_queries(
            embedding, 
            user_id="test_user", 
            limit=5
        )
        
        print(f"✅ Similar queries found: {len(similar_queries)}")
        if similar_queries:
            for i, query in enumerate(similar_queries[:3]):
                print(f"   {i+1}. Similarity: {query.get('similarity', 0):.3f}")
                print(f"      Query: {query.get('query_text', '')[:50]}...")
        
        print("\n🎉 All tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        print("and have activated the virtual environment")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_cosine_similarity():
    """Test cosine similarity calculation"""
    print("\n🧮 Test: Cosine Similarity Calculation")
    
    try:
        from rag_service import rag_service
        
        # Test vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]  # Same direction
        vec3 = [-1.0, 0.0, 0.0]  # Opposite direction
        vec4 = [0.0, 1.0, 0.0]  # Perpendicular
        
        # Calculate similarities
        sim1 = rag_service._calculate_cosine_similarity(vec1, vec2)  # Should be 1.0
        sim2 = rag_service._calculate_cosine_similarity(vec1, vec3)  # Should be -1.0
        sim3 = rag_service._calculate_cosine_similarity(vec1, vec4)  # Should be 0.0
        
        print(f"✅ Similarity calculations:")
        print(f"   vec1 vs vec2 (same): {sim1:.3f} (expected: 1.000)")
        print(f"   vec1 vs vec3 (opposite): {sim2:.3f} (expected: -1.000)")
        print(f"   vec1 vs vec4 (perpendicular): {sim3:.3f} (expected: 0.000)")
        
    except Exception as e:
        print(f"❌ Cosine similarity test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Vector Search Tests")
    print("Make sure you have:")
    print("1. Activated the virtual environment")
    print("2. Set up your .env file with database credentials")
    print("3. Started the required database services")
    print()
    
    # Test cosine similarity first (no database required)
    test_cosine_similarity()
    
    # Test vector search (requires database)
    try:
        asyncio.run(test_vector_search())
    except Exception as e:
        print(f"\n❌ Vector search tests failed: {e}")
        print("This might be due to database connection issues.")
        print("Check your .env file and database services.")
