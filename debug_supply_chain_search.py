#!/usr/bin/env python3
"""
Debug script for supply chain search issue
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def debug_supply_chain_search():
    """Debug the supply chain search issue"""
    
    print("🔍 Debugging Supply Chain Search Issue")
    print("=" * 50)
    
    try:
        from postgres import postgres_service
        from openai_service import openai_service
        
        print("✅ Services imported successfully")
        
        # Test query
        test_query = "supply chain"
        print(f"\n🔍 Test query: {test_query}")
        
        # Generate embedding for the query
        print("\n1️⃣ Generating embedding for query...")
        query_embedding = openai_service.get_embedding(test_query)
        print(f"✅ Embedding generated: {len(query_embedding)} dimensions")
        print(f"   First 5 values: {query_embedding[:5]}")
        
        # Check database statistics
        print("\n2️⃣ Checking vector database statistics...")
        stats = postgres_service.get_search_statistics()
        print(f"📊 Database stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test risk search specifically
        print("\n3️⃣ Testing risk search for supply chain...")
        similar_risks = postgres_service.search_similar_risks(query_embedding, limit=10)
        print(f"🔍 Similar risks found: {len(similar_risks)}")
        
        if similar_risks:
            print("   Top results:")
            for i, risk in enumerate(similar_risks[:5]):
                print(f"   {i+1}. Similarity: {risk.get('similarity', 0):.3f}")
                print(f"      Description: {risk.get('description', 'Unknown')[:80]}...")
                print(f"      Category: {risk.get('category', 'Unknown')}")
                print(f"      Risk ID: {risk.get('risk_id', 'Unknown')}")
        else:
            print("   ❌ No risks found!")
        
        # Test control search
        print("\n4️⃣ Testing control search for supply chain...")
        similar_controls = postgres_service.search_similar_controls(query_embedding, limit=10)
        print(f"🔍 Similar controls found: {len(similar_controls)}")
        
        if similar_controls:
            print("   Top results:")
            for i, control in enumerate(similar_controls[:5]):
                print(f"   {i+1}. Similarity: {control.get('similarity', 0):.3f}")
                print(f"      Title: {control.get('title', 'Unknown')[:80]}...")
                print(f"      Description: {control.get('description', 'Unknown')[:80]}...")
                print(f"      Control ID: {control.get('control_id', 'Unknown')}")
        else:
            print("   ❌ No controls found!")
        
        # Test guidance search
        print("\n5️⃣ Testing ISO guidance search for supply chain...")
        similar_guidance = postgres_service.get_iso_guidance(query_embedding, limit=10)
        print(f"🔍 Similar guidance found: {len(similar_guidance)}")
        
        if similar_guidance:
            print("   Top results:")
            for i, guidance in enumerate(similar_guidance[:5]):
                print(f"   {i+1}. Similarity: {guidance.get('similarity', 0):.3f}")
                print(f"      Annex: {guidance.get('annex_reference', 'Unknown')}")
                print(f"      Text: {guidance.get('guidance_text', 'Unknown')[:80]}...")
        else:
            print("   ❌ No guidance found!")
        
        # Test with different query variations
        print("\n6️⃣ Testing with different query variations...")
        variations = [
            "supply chain security",
            "supplier relationships",
            "vendor management",
            "third party risk",
            "supply chain risk"
        ]
        
        for variation in variations:
            print(f"\n   Testing: '{variation}'")
            var_embedding = openai_service.get_embedding(variation)
            var_risks = postgres_service.search_similar_risks(var_embedding, limit=3)
            print(f"      Risks found: {len(var_risks)}")
            if var_risks:
                top_risk = var_risks[0]
                print(f"      Top similarity: {top_risk.get('similarity', 0):.3f}")
        
        # Check if there are any supply chain related entries in the database
        print("\n7️⃣ Checking for supply chain related data...")
        
        # Try to find any entries with "supply" or "chain" in the text
        # This would require a text search, but let's check what we can
        
        print("\n8️⃣ Recommendations for fixing the issue:")
        print("   • Check if supply chain data has proper embeddings")
        print("   • Verify similarity thresholds are not too high")
        print("   • Ensure embeddings are stored correctly")
        print("   • Check if the data is in the right format")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

def test_direct_database_query():
    """Test direct database queries to see what's actually stored"""
    
    print("\n🔍 Testing Direct Database Queries")
    print("=" * 40)
    
    try:
        from postgres import postgres_service
        
        if not postgres_service.conn:
            print("❌ No database connection available")
            return
        
        # Check what's actually in the risk_embeddings table
        print("\n📊 Checking risk_embeddings table content...")
        
        with postgres_service.conn.cursor() as cur:
            # Check table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'risk_embeddings'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print("   Table structure:")
            for col in columns:
                print(f"     {col[0]}: {col[1]}")
            
            # Check if table has data
            cur.execute("SELECT COUNT(*) FROM risk_embeddings")
            count = cur.fetchone()[0]
            print(f"\n   Total risks in table: {count}")
            
            if count > 0:
                # Look for supply chain related entries
                cur.execute("""
                    SELECT risk_id, description, category, user_id
                    FROM risk_embeddings 
                    WHERE description ILIKE '%supply%' 
                       OR description ILIKE '%chain%'
                       OR category ILIKE '%supply%'
                       OR category ILIKE '%chain%'
                    LIMIT 5
                """)
                supply_chain_risks = cur.fetchall()
                
                print(f"\n   Supply chain related risks found: {len(supply_chain_risks)}")
                for risk in supply_chain_risks:
                    print(f"     Risk ID: {risk[0]}")
                    print(f"     Description: {risk[1][:100]}...")
                    print(f"     Category: {risk[2]}")
                    print(f"     User ID: {risk[3]}")
                    print()
                
                # Check a few random entries to see the data quality
                cur.execute("""
                    SELECT risk_id, description, category, user_id
                    FROM risk_embeddings 
                    LIMIT 3
                """)
                sample_risks = cur.fetchall()
                
                print("   Sample risks from table:")
                for risk in sample_risks:
                    print(f"     Risk ID: {risk[0]}")
                    print(f"     Description: {risk[1][:100]}...")
                    print(f"     Category: {risk[2]}")
                    print(f"     User ID: {risk[3]}")
                    print()
        
    except Exception as e:
        print(f"❌ Direct database query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Supply Chain Search Debug")
    print("This script will help identify why supply chain searches aren't working")
    print()
    
    # Run the main debug
    debug_supply_chain_search()
    
    # Run direct database queries
    test_direct_database_query()
    
    print("\n🎯 Debug completed!")
    print("Check the output above to identify the issue with supply chain searches.")
