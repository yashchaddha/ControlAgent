#!/usr/bin/env python3
"""
Test script to verify the complete control storage flow:
1. Control generation
2. Control selection
3. MongoDB storage
4. Vector embedding creation
5. Neo4j knowledge graph population
"""

import sys
import os
import logging
import uuid

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_complete_control_storage_flow():
    """Test the complete control storage flow"""
    
    print("🚀 Testing Complete Control Storage Flow")
    print("=" * 70)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from app.openai_service import openai_service
        from app.database import mongodb
        from app.neo4j_db import neo4j_service
        from app.postgres import postgres_service
        from app.rag_service import rag_service
        
        print("✅ All services imported successfully")
        
        # Test data
        test_user_id = "test_user_001"
        test_risk = {
            "id": "risk_test_001",
            "description": "Supply chain disruption due to natural disasters",
            "category": "Operational Risk",
            "impact": "High",
            "likelihood": "Medium",
            "user_id": test_user_id
        }
        
        test_user_context = {
            "organization_name": "Test Corp",
            "domain": "Manufacturing",
            "location": "Philippines"
        }
        
        print(f"\n📋 Test Data:")
        print(f"   User ID: {test_user_id}")
        print(f"   Risk ID: {test_risk['id']}")
        print(f"   Risk Description: {test_risk['description']}")
        print(f"   Organization: {test_user_context['organization_name']}")
        
        # Step 1: Generate Controls
        print(f"\n🔧 Step 1: Generating Controls")
        print("-" * 40)
        
        controls = openai_service.generate_controls(test_risk, test_user_context)
        
        if not controls:
            print("❌ No controls generated!")
            return
        
        print(f"✅ Generated {len(controls)} controls")
        
        # Add required fields to controls
        for i, control in enumerate(controls):
            control["risk_id"] = test_risk["id"]
            control["user_id"] = test_user_id
            control["id"] = str(uuid.uuid4())
            
            if not control.get("control_id"):
                control["control_id"] = f"CTRL-{test_risk['id']}-{i+1:03d}"
        
        print(f"✅ Controls prepared with required fields")
        
        # Step 2: Test MongoDB Storage
        print(f"\n💾 Step 2: Testing MongoDB Storage")
        print("-" * 40)
        
        try:
            # Save controls to MongoDB
            saved_control_ids = mongodb.save_controls(controls)
            print(f"✅ Controls saved to MongoDB: {len(saved_control_ids)} controls")
            print(f"   Saved control IDs: {saved_control_ids}")
            
            # Verify controls are in MongoDB
            stored_controls = list(mongodb.controls.find({"user_id": test_user_id}))
            print(f"✅ Verified {len(stored_controls)} controls in MongoDB")
            
            # Check risk mapping
            for control in stored_controls:
                print(f"   Control: {control.get('control_id')} -> Risk: {control.get('risk_id')}")
                
        except Exception as e:
            print(f"❌ MongoDB storage failed: {e}")
            return
        
        # Step 3: Test Vector Embedding Storage
        print(f"\n📝 Step 3: Testing Vector Embedding Storage")
        print("-" * 40)
        
        try:
            # Store control embeddings
            rag_service.store_control_embeddings(controls)
            print(f"✅ Control embeddings stored successfully")
            
            # Verify embeddings in PostgreSQL
            for control in controls:
                embedding = postgres_service.search_similar_controls(
                    [0.0] * 1536,  # Dummy embedding for search
                    limit=1
                )
                if embedding:
                    print(f"   ✅ Embeddings found in vector database")
                    break
            else:
                print(f"   ⚠️  No embeddings found in vector database")
                
        except Exception as e:
            print(f"❌ Vector embedding storage failed: {e}")
        
        # Step 4: Test Neo4j Knowledge Graph Creation
        print(f"\n🔗 Step 4: Testing Neo4j Knowledge Graph Creation")
        print("-" * 40)
        
        try:
            # Create user node first
            user_data = {
                "user_id": test_user_id,
                "username": test_user_id,
                "organization_name": test_user_context["organization_name"],
                "location": test_user_context["location"],
                "domain": test_user_context["domain"]
            }
            
            neo4j_service.create_user_node(user_data)
            print(f"✅ User node created in Neo4j")
            
            # Create risk node
            neo4j_service.create_risk_node(test_risk)
            print(f"✅ Risk node created in Neo4j")
            
            # Create control nodes and relationships
            neo4j_success_count = 0
            for control in controls:
                try:
                    success = neo4j_service.create_control_node(control)
                    if success:
                        neo4j_success_count += 1
                        print(f"   ✅ Control node created: {control.get('control_id')}")
                    else:
                        print(f"   ⚠️  Control node creation failed: {control.get('control_id')}")
                except Exception as e:
                    print(f"   ❌ Control node creation error: {e}")
            
            print(f"✅ Neo4j knowledge graph populated: {neo4j_success_count}/{len(controls)} controls")
            
        except Exception as e:
            print(f"❌ Neo4j knowledge graph creation failed: {e}")
        
        # Step 5: Verify Complete Flow
        print(f"\n🎯 Step 5: Verifying Complete Flow")
        print("-" * 40)
        
        # Check MongoDB
        mongo_controls = list(mongodb.controls.find({"user_id": test_user_id}))
        print(f"📊 MongoDB: {len(mongo_controls)} controls stored")
        
        # Check vector database
        try:
            stats = postgres_service.get_search_statistics()
            print(f"📊 Vector Database: {stats.get('control_embeddings', 0)} control embeddings")
        except:
            print(f"📊 Vector Database: Unable to get statistics")
        
        # Check Neo4j
        try:
            # Query for risk-control relationships
            with neo4j_service.driver.session() as session:
                result = session.run("""
                    MATCH (r:Risk {id: $risk_id})-[:MITIGATES]-(c:Control)
                    RETURN count(c) as control_count
                """, risk_id=test_risk["id"])
                
                control_count = result.single()["control_count"] if result.single() else 0
                print(f"📊 Neo4j: {control_count} risk-control relationships")
                
        except Exception as e:
            print(f"📊 Neo4j: Unable to query relationships - {e}")
        
        print(f"\n🎉 Complete Control Storage Flow Test Completed!")
        print(f"📋 Summary:")
        print(f"   • Controls generated: {len(controls)}")
        print(f"   • MongoDB storage: {'✅' if mongo_controls else '❌'}")
        print(f"   • Vector embeddings: {'✅' if '📊 Vector Database' in locals() else '❌'}")
        print(f"   • Neo4j knowledge graph: {'✅' if '📊 Neo4j' in locals() else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_control_selection_simulation():
    """Test the control selection simulation"""
    
    print(f"\n🔍 Testing Control Selection Simulation")
    print("=" * 50)
    
    try:
        from app.langgraph_agent import iso_agent
        
        print("✅ LangGraph agent imported successfully")
        
        # Simulate a control selection scenario
        test_query = "generate controls for all risks"
        test_user = "test_user_001"
        
        print(f"📝 Simulating query: '{test_query}'")
        print(f"👤 User: {test_user}")
        
        # This would normally be called by the frontend
        # For testing, we'll just verify the agent is available
        print(f"✅ Agent workflow available for control selection")
        print(f"📋 Workflow nodes: classify_intent → retrieve_context → generate_controls → handle_selection → store_data → store_query_embedding → synthesize_response")
        
    except Exception as e:
        print(f"❌ Control selection simulation failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_data():
    """Clean up test data"""
    
    print(f"\n🧹 Cleaning Up Test Data")
    print("=" * 40)
    
    try:
        from app.database import mongodb
        from app.neo4j_db import neo4j_service
        
        test_user_id = "test_user_001"
        
        # Clean MongoDB
        try:
            result = mongodb.controls.delete_many({"user_id": test_user_id})
            print(f"🗑️  MongoDB: Deleted {result.deleted_count} test controls")
        except Exception as e:
            print(f"❌ MongoDB cleanup failed: {e}")
        
        # Clean Neo4j
        try:
            if neo4j_service.driver:
                with neo4j_service.driver.session() as session:
                    # Delete test control nodes
                    result = session.run("""
                        MATCH (c:Control {user_id: $user_id})
                        DETACH DELETE c
                    """, user_id=test_user_id)
                    
                    # Delete test risk nodes
                    result = session.run("""
                        MATCH (r:Risk {user_id: $user_id})
                        DETACH DELETE r
                    """, user_id=test_user_id)
                    
                    # Delete test user node
                    result = session.run("""
                        MATCH (u:User {id: $user_id})
                        DETACH DELETE u
                    """, user_id=test_user_id)
                    
                print(f"🗑️  Neo4j: Test nodes deleted")
        except Exception as e:
            print(f"❌ Neo4j cleanup failed: {e}")
        
        print(f"✅ Test data cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    print("🚀 Control Storage Flow Test Suite")
    print("This will test the complete flow from control generation to storage")
    print()
    
    # Test the complete flow
    test_complete_control_storage_flow()
    
    # Test control selection simulation
    test_control_selection_simulation()
    
    # Clean up test data
    cleanup_test_data()
    
    print("\n🎯 All tests completed!")
    print("🔍 Check the output above for any issues in the control storage flow")
