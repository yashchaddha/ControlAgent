#!/usr/bin/env python3
"""
Script to fix existing vector embeddings in the database
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_vector_embeddings():
    """Fix existing embeddings by recasting them to vector type"""
    print("🔧 Fixing Vector Embeddings in Database")
    print("=" * 50)
    
    try:
        # Connect to database
        postgres_uri = os.getenv("POSTGRES_URI")
        if not postgres_uri:
            print("❌ POSTGRES_URI not found in environment variables")
            return
        
        print("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(postgres_uri)
        print("   ✅ Database connected successfully")
        
        with conn.cursor() as cur:
            # Check current embedding types
            print("\n📊 Checking current embedding types...")
            
            # Check control embeddings
            cur.execute("SELECT COUNT(*) FROM control_embeddings;")
            control_count = cur.fetchone()[0]
            print(f"   📋 Control embeddings: {control_count}")
            
            if control_count > 0:
                cur.execute("SELECT embedding FROM control_embeddings LIMIT 1;")
                sample = cur.fetchone()
                if sample:
                    print(f"   📊 Sample control embedding type: {type(sample[0])}")
                    print(f"   📊 Sample control embedding value: {str(sample[0])[:100]}...")
            
            # Check risk embeddings
            cur.execute("SELECT COUNT(*) FROM risk_embeddings;")
            risk_count = cur.fetchone()[0]
            print(f"   📋 Risk embeddings: {risk_count}")
            
            if risk_count > 0:
                cur.execute("SELECT embedding FROM risk_embeddings LIMIT 1;")
                sample = cur.fetchone()
                if sample:
                    print(f"   📊 Sample risk embedding type: {type(sample[0])}")
                    print(f"   📊 Sample risk embedding value: {str(sample[0])[:100]}...")
            
            # Check ISO guidance embeddings
            cur.execute("SELECT COUNT(*) FROM iso_guidance_embeddings;")
            guidance_count = cur.fetchone()[0]
            print(f"   📋 ISO guidance embeddings: {guidance_count}")
            
            if guidance_count > 0:
                cur.execute("SELECT embedding FROM iso_guidance_embeddings LIMIT 1;")
                sample = cur.fetchone()
                if sample:
                    print(f"   📊 Sample guidance embedding type: {type(sample[0])}")
                    print(f"   📊 Sample guidance embedding value: {str(sample[0])[:100]}...")
            
            # Fix control embeddings
            if control_count > 0:
                print(f"\n🔧 Fixing control embeddings...")
                try:
                    # Create a temporary table with proper vector type
                    cur.execute("""
                        CREATE TEMP TABLE temp_control_embeddings AS
                        SELECT id, control_id, user_id, title, description, annex_reference, 
                               domain_category, embedding::vector as embedding, created_at, updated_at
                        FROM control_embeddings;
                    """)
                    
                    # Clear the original table
                    cur.execute("DELETE FROM control_embeddings;")
                    
                    # Insert back with proper vector type
                    cur.execute("""
                        INSERT INTO control_embeddings 
                        SELECT * FROM temp_control_embeddings;
                    """)
                    
                    # Drop temp table
                    cur.execute("DROP TABLE temp_control_embeddings;")
                    
                    print("   ✅ Control embeddings fixed successfully")
                    
                except Exception as e:
                    print(f"   ❌ Error fixing control embeddings: {e}")
                    conn.rollback()
                    return
            
            # Fix risk embeddings
            if risk_count > 0:
                print(f"🔧 Fixing risk embeddings...")
                try:
                    # Create a temporary table with proper vector type
                    cur.execute("""
                        CREATE TEMP TABLE temp_risk_embeddings AS
                        SELECT id, risk_id, user_id, description, category, domain,
                               embedding::vector as embedding, created_at, updated_at
                        FROM risk_embeddings;
                    """)
                    
                    # Clear the original table
                    cur.execute("DELETE FROM risk_embeddings;")
                    
                    # Insert back with proper vector type
                    cur.execute("""
                        INSERT INTO risk_embeddings 
                        SELECT * FROM temp_risk_embeddings;
                    """)
                    
                    # Drop temp table
                    cur.execute("DROP TABLE temp_risk_embeddings;")
                    
                    print("   ✅ Risk embeddings fixed successfully")
                    
                except Exception as e:
                    print(f"   ❌ Error fixing risk embeddings: {e}")
                    conn.rollback()
                    return
            
            # Fix ISO guidance embeddings
            if guidance_count > 0:
                print(f"🔧 Fixing ISO guidance embeddings...")
                try:
                    # Create a temporary table with proper vector type
                    cur.execute("""
                        CREATE TEMP TABLE temp_guidance_embeddings AS
                        SELECT id, annex_reference, guidance_text, 
                               embedding::vector as embedding, created_at
                        FROM iso_guidance_embeddings;
                    """)
                    
                    # Clear the original table
                    cur.execute("DELETE FROM iso_guidance_embeddings;")
                    
                    # Insert back with proper vector type
                    cur.execute("""
                        INSERT INTO iso_guidance_embeddings 
                        SELECT * FROM temp_guidance_embeddings;
                    """)
                    
                    # Drop temp table
                    cur.execute("DROP TABLE temp_guidance_embeddings;")
                    
                    print("   ✅ ISO guidance embeddings fixed successfully")
                    
                except Exception as e:
                    print(f"   ❌ Error fixing ISO guidance embeddings: {e}")
                    conn.rollback()
                    return
            
            # Commit all changes
            conn.commit()
            print("\n✅ All embeddings fixed successfully!")
            
            # Test vector search
            print(f"\n🧪 Testing vector search after fix...")
            try:
                # Create a test embedding
                test_embedding = [0.1] * 1536
                
                # Test control search
                cur.execute("""
                    SELECT control_id, title, 
                           1 - (embedding <=> %s::vector) as similarity
                    FROM control_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT 3
                """, (test_embedding, test_embedding))
                
                results = cur.fetchall()
                print(f"   ✅ Control vector search test: {len(results)} results")
                
                if results:
                    for i, result in enumerate(results):
                        print(f"      Result {i+1}: {result[0]} - {result[1][:50]}... (similarity: {result[2]:.3f})")
                
                # Test risk search
                cur.execute("""
                    SELECT risk_id, description, 
                           1 - (embedding <=> %s::vector) as similarity
                    FROM risk_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT 3
                """, (test_embedding, test_embedding))
                
                results = cur.fetchall()
                print(f"   ✅ Risk vector search test: {len(results)} results")
                
            except Exception as e:
                print(f"   ❌ Vector search test failed: {e}")
        
        conn.close()
        print("\n🎉 Vector embeddings fix completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Failed to fix vector embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_vector_embeddings()
