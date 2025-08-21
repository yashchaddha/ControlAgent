#!/usr/bin/env python3
"""
Test script to verify vector search fix
"""

import asyncio
import sys
import os

async def test_vector_search_fix():
    """Test if vector search is working after the fix"""
    print("🧪 Testing Vector Search Fix")
    print("=" * 50)
    
    try:
        # Add app to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        # Test PostgreSQL service
        print("🔧 Testing PostgreSQL Service...")
        from postgres import postgres_service
        print("   ✅ PostgreSQL service imported successfully")
        
        # Test if we can connect and check embeddings
        print(f"\n🔍 Testing database connection...")
        if postgres_service.conn:
            print("   ✅ Database connected")
            
            # Check control embeddings table
            with postgres_service.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM control_embeddings;")
                count = cur.fetchone()[0]
                print(f"   📋 Control embeddings count: {count}")
                
                if count > 0:
                    # Check embedding type
                    cur.execute("SELECT embedding FROM control_embeddings LIMIT 1;")
                    sample = cur.fetchone()
                    if sample:
                        print(f"   📊 Sample embedding type: {type(sample[0])}")
                        print(f"   📊 Sample embedding value: {str(sample[0])[:100]}...")
                        
                        # Test if we can cast to vector
                        try:
                            cur.execute("SELECT %s::vector as test_vector;", (sample[0],))
                            test_result = cur.fetchone()
                            print(f"   ✅ Vector casting test: {type(test_result[0])}")
                        except Exception as e:
                            print(f"   ❌ Vector casting failed: {e}")
                    
                    # Test a simple vector search
                    print(f"\n🔍 Testing simple vector search...")
                    try:
                        # Create a test embedding
                        test_embedding = [0.1] * 1536
                        
                        # Test the search
                        cur.execute("""
                            SELECT control_id, title, 
                                   1 - (embedding <=> %s::vector) as similarity
                            FROM control_embeddings
                            ORDER BY embedding <=> %s::vector
                            LIMIT 3
                        """, (test_embedding, test_embedding))
                        
                        results = cur.fetchall()
                        print(f"   ✅ Vector search test successful: {len(results)} results")
                        
                        if results:
                            for i, result in enumerate(results):
                                print(f"      Result {i+1}: {result[0]} - {result[1][:50]}... (similarity: {result[2]:.3f})")
                        
                    except Exception as e:
                        print(f"   ❌ Vector search test failed: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("   ⚠️  No control embeddings found")
        else:
            print("   ❌ Database not connected")
        
        print("\n✅ Vector search fix test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vector_search_fix())
