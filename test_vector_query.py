#!/usr/bin/env python3
"""
Simple test to debug vector search query directly
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_vector_query_directly():
    """Test the vector search query directly"""
    
    print("🔍 Testing Vector Search Query Directly")
    print("=" * 40)
    
    try:
        from app.postgres import postgres_service
        from app.openai_service import openai_service
        
        if not postgres_service.conn:
            print("❌ No database connection")
            return
        
        print("✅ Database connected")
        
        # Generate a test embedding
        test_query = "supply chain"
        test_embedding = openai_service.get_embedding(test_query)
        print(f"✅ Test embedding generated: {len(test_embedding)} dimensions")
        print(f"   First 5 values: {test_embedding[:5]}")
        
        # Test the vector search query directly
        print("\n📊 Testing vector search query directly:")
        
        with postgres_service.conn.cursor() as cur:
            # First, check if we can see the data
            print("1️⃣ Checking if data exists:")
            cur.execute("SELECT COUNT(*) FROM risk_embeddings")
            count = cur.fetchone()[0]
            print(f"   Risk embeddings count: {count}")
            
            if count > 0:
                print("2️⃣ Checking actual data:")
                cur.execute("SELECT risk_id, description FROM risk_embeddings LIMIT 2")
                risks = cur.fetchall()
                for i, risk in enumerate(risks):
                    print(f"   Risk {i+1}: {risk[0]} - {risk[1][:50]}...")
                
                print("3️⃣ Testing vector similarity query:")
                try:
                    # Test the exact query from the search function
                    cur.execute("""
                        SELECT risk_id, user_id, description, category,
                               1 - (embedding <=> %s::vector) as similarity
                        FROM risk_embeddings
                        ORDER BY embedding <=> %s::vector
                        LIMIT 5
                    """, (test_embedding, test_embedding))
                    
                    results = cur.fetchall()
                    print(f"   Query executed successfully, returned {len(results)} results")
                    
                    if results:
                        print("   Top results:")
                        for i, result in enumerate(results[:3]):
                            print(f"     {i+1}. Similarity: {result[4]:.3f}")
                            print(f"        Description: {result[2][:60]}...")
                    else:
                        print("   ❌ No results returned from query")
                        
                except Exception as e:
                    print(f"   ❌ Vector query failed: {e}")
                    print(f"   Error type: {type(e).__name__}")
                    
                    # Try a simpler query to see what's wrong
                    print("\n4️⃣ Testing simpler vector query:")
                    try:
                        cur.execute("SELECT embedding FROM risk_embeddings LIMIT 1")
                        embedding_sample = cur.fetchone()
                        if embedding_sample:
                            print(f"   ✅ Can read embeddings from table")
                            print(f"   Embedding type: {type(embedding_sample[0])}")
                        else:
                            print("   ❌ No embeddings found")
                    except Exception as e2:
                        print(f"   ❌ Simple embedding read failed: {e2}")
            else:
                print("   ❌ No risk embeddings found in table")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Vector Query Direct Test")
    print("This will test the vector search query directly")
    print()
    
    test_vector_query_directly()
    
    print("\n�� Test completed!")
