#!/usr/bin/env python3
"""
Debug script to examine database content directly
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def examine_database_content():
    """Examine the actual database content"""
    
    print("🔍 Examining Database Content")
    print("=" * 40)
    
    try:
        from app.postgres import postgres_service
        
        if not postgres_service.conn:
            print("❌ No database connection")
            return
        
        print("✅ Database connected")
        
        # Check table structure
        print("\n📊 Table Structure:")
        with postgres_service.conn.cursor() as cur:
            cur.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('risk_embeddings', 'control_embeddings', 'iso_guidance_embeddings')
                ORDER BY table_name, ordinal_position
            """)
            columns = cur.fetchall()
            
            current_table = None
            for col in columns:
                if col[0] != current_table:
                    current_table = col[0]
                    print(f"\n   Table: {current_table}")
                print(f"     {col[1]}: {col[2]}")
        
        # Check actual data in risk_embeddings
        print("\n📊 Risk Embeddings Content:")
        with postgres_service.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM risk_embeddings")
            count = cur.fetchone()[0]
            print(f"   Total records: {count}")
            
            if count > 0:
                cur.execute("""
                    SELECT risk_id, description, category, user_id
                    FROM risk_embeddings
                """)
                risks = cur.fetchall()
                
                for i, risk in enumerate(risks):
                    print(f"\n   Risk {i+1}:")
                    print(f"     ID: {risk[0]}")
                    print(f"     Description: {risk[1][:100]}...")
                    print(f"     Category: {risk[2]}")
                    print(f"     User ID: {risk[3]}")
                    print(f"     Has embedding: Yes (pgvector type)")
        
        # Check control embeddings
        print("\n📊 Control Embeddings Content:")
        with postgres_service.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM control_embeddings")
            count = cur.fetchone()[0]
            print(f"   Total records: {count}")
            
            if count > 0:
                cur.execute("""
                    SELECT control_id, title, description, user_id
                    FROM control_embeddings
                """)
                controls = cur.fetchall()
                
                for i, control in enumerate(controls):
                    print(f"\n   Control {i+1}:")
                    print(f"     ID: {control[0]}")
                    print(f"     Title: {control[1][:100]}...")
                    print(f"     Description: {control[2][:100]}...")
                    print(f"     User ID: {control[3]}")
                    print(f"     Has embedding: Yes (pgvector type)")
        
        # Check ISO guidance embeddings
        print("\n📊 ISO Guidance Embeddings Content:")
        with postgres_service.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM iso_guidance_embeddings")
            count = cur.fetchone()[0]
            print(f"   Total records: {count}")
            
            if count > 0:
                cur.execute("""
                    SELECT annex_reference, guidance_text
                    FROM iso_guidance_embeddings
                """)
                guidance = cur.fetchall()
                
                for i, g in enumerate(guidance):
                    print(f"\n   Guidance {i+1}:")
                    print(f"     Annex: {g[0]}")
                    print(f"     Text: {g[1][:100]}...")
                    print(f"     Has embedding: Yes (pgvector type)")
        
    except Exception as e:
        print(f"❌ Database examination failed: {e}")
        import traceback
        traceback.print_exc()

def test_search_functions():
    """Test the search functions directly"""
    
    print("\n🔍 Testing Search Functions Directly")
    print("=" * 40)
    
    try:
        from app.postgres import postgres_service
        from app.openai_service import openai_service
        
        # Generate a test embedding
        test_query = "supply chain"
        test_embedding = openai_service.get_embedding(test_query)
        print(f"✅ Test embedding generated: {len(test_embedding)} dimensions")
        
        # Test risk search directly
        print("\n📊 Testing Risk Search:")
        try:
            risks = postgres_service.search_similar_risks(test_embedding, limit=10)
            print(f"   Search returned: {len(risks)} results")
            
            if risks:
                print("   Top result:")
                top_risk = risks[0]
                print(f"     Similarity: {top_risk.get('similarity', 0):.3f}")
                print(f"     Description: {top_risk.get('description', 'Unknown')[:80]}...")
            else:
                print("   ❌ No results returned")
                
        except Exception as e:
            print(f"   ❌ Risk search failed: {e}")
        
        # Test control search directly
        print("\n📊 Testing Control Search:")
        try:
            controls = postgres_service.search_similar_controls(test_embedding, limit=10)
            print(f"   Search returned: {len(controls)} results")
            
            if controls:
                print("   Top result:")
                top_control = controls[0]
                print(f"     Similarity: {top_control.get('similarity', 0):.3f}")
                print(f"     Title: {top_control.get('title', 'Unknown')[:80]}...")
            else:
                print("   ❌ No results returned")
                
        except Exception as e:
            print(f"   ❌ Control search failed: {e}")
        
        # Test guidance search directly
        print("\n📊 Testing Guidance Search:")
        try:
            guidance = postgres_service.get_iso_guidance(test_embedding, limit=10)
            print(f"   Search returned: {len(guidance)} results")
            
            if risks:
                print("   Top result:")
                top_guidance = guidance[0]
                print(f"     Similarity: {top_guidance.get('similarity', 0):.3f}")
                print(f"     Annex: {top_guidance.get('annex_reference', 'Unknown')}")
            else:
                print("   ❌ No results returned")
                
        except Exception as e:
            print(f"   ❌ Guidance search failed: {e}")
        
    except Exception as e:
        print(f"❌ Search function testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Database Content Examination")
    print("This will show what's actually in the vector database")
    print()
    
    # Examine database content
    examine_database_content()
    
    # Test search functions
    test_search_functions()
    
    print("\n🎯 Database examination completed!")
