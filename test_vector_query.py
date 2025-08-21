#!/usr/bin/env python3
"""
Simple test script to test vector search directly
"""

import psycopg2
import os
from dotenv import load_dotenv

def test_vector_search():
    """Test vector search directly"""
    print("🧪 Testing Vector Search Directly")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Connect to database
        postgres_uri = os.getenv("POSTGRES_URI")
        if not postgres_uri:
            print("❌ POSTGRES_URI not found")
            return
        
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(postgres_uri)
        print("   ✅ Connected successfully")
        
        with conn.cursor() as cur:
            # Check embedding type
            print("\n📊 Checking embedding type...")
            cur.execute("SELECT embedding FROM control_embeddings LIMIT 1")
            emb = cur.fetchone()
            if emb:
                print(f"   Embedding type: {type(emb[0])}")
                print(f"   Embedding value: {str(emb[0])[:100]}...")
            else:
                print("   ❌ No embeddings found")
                return
            
            # Test vector search
            print("\n🔍 Testing vector search...")
            test_emb = [0.1] * 1536
            print(f"   Test embedding length: {len(test_emb)}")
            
            try:
                # Test the vector similarity operator
                cur.execute("""
                    SELECT control_id, title, 
                           1 - (embedding <=> %s::vector) as similarity
                    FROM control_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT 3
                """, (test_emb, test_emb))
                
                results = cur.fetchall()
                print(f"   ✅ Vector search successful: {len(results)} results")
                
                for i, result in enumerate(results):
                    print(f"      Result {i+1}: {result[0]} - {result[1][:50]}... (similarity: {result[2]:.3f})")
                    
            except Exception as e:
                print(f"   ❌ Vector search failed: {e}")
                import traceback
                traceback.print_exc()
        
        conn.close()
        print("\n✅ Vector search test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vector_search()
