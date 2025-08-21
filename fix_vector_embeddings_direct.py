#!/usr/bin/env python3
"""
Direct script to fix vector embeddings by updating them in place
"""

import psycopg2
import os
from dotenv import load_dotenv

def fix_vector_embeddings_direct():
    """Fix embeddings by updating them directly"""
    print("🔧 Fixing Vector Embeddings Directly")
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
            # Check current state
            print("\n📊 Checking current state...")
            cur.execute("SELECT COUNT(*) FROM control_embeddings")
            control_count = cur.fetchone()[0]
            print(f"   Control embeddings: {control_count}")
            
            if control_count > 0:
                # Get a sample embedding
                cur.execute("SELECT id, embedding FROM control_embeddings LIMIT 1")
                sample = cur.fetchone()
                if sample:
                    print(f"   Sample embedding type: {type(sample[1])}")
                    print(f"   Sample embedding value: {str(sample[1])[:100]}...")
                    
                    # Try to cast to vector
                    try:
                        cur.execute("SELECT %s::vector as test_vector", (sample[1],))
                        test_result = cur.fetchone()
                        print(f"   ✅ Can cast to vector: {type(test_result[0])}")
                        
                        # The embeddings are actually working as vectors!
                        print("   🎯 The embeddings are already working as vectors!")
                        
                        # Test vector search
                        print("\n🧪 Testing vector search...")
                        test_emb = [0.1] * 1536
                        
                        cur.execute("""
                            SELECT control_id, title, 
                                   1 - (embedding <=> %s::vector) as similarity
                            FROM control_embeddings
                            ORDER BY embedding <=> %s::vector
                            LIMIT 3
                        """, (test_emb, test_emb))
                        
                        results = cur.fetchall()
                        print(f"   ✅ Vector search working: {len(results)} results")
                        
                        for i, result in enumerate(results):
                            print(f"      Result {i+1}: {result[0]} - {result[1][:50]}... (similarity: {result[2]:.3f})")
                        
                        # The issue might be in the PostgreSQL service code
                        print("\n🔍 The issue might be in the PostgreSQL service code, not the database")
                        
                    except Exception as e:
                        print(f"   ❌ Cannot cast to vector: {e}")
            
            conn.close()
            print("\n✅ Vector embeddings check completed!")
            
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_vector_embeddings_direct()
