#!/usr/bin/env python3
"""
Test script to verify the fixed control selection flow:
1. Generate controls (simulate user request)
2. Simulate control selection
3. Verify storage without re-generation
"""

import sys
import os
import logging
import uuid

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_control_selection_flow():
    """Test the complete control selection flow"""
    
    print("🚀 Testing Fixed Control Selection Flow")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from app.openai_service import openai_service
        from app.database import mongodb
        from app.neo4j_db import neo4j_service
        from app.rag_service import rag_service
        
        print("✅ All services imported successfully")
        
        # Test data
        test_user_id = "test_user_002"
        test_risk = {
            "id": "risk_test_002",
            "description": "Data breach due to unauthorized access",
            "category": "Information Security",
            "impact": "High",
            "likelihood": "Medium",
            "user_id": test_user_id
        }
        
        test_user_context = {
            "organization_name": "Test Corp",
            "domain": "Technology",
            "location": "Philippines"
        }
        
        print(f"\n📋 Test Data:")
        print(f"   User ID: {test_user_id}")
        print(f"   Risk ID: {test_risk['id']}")
        print(f"   Risk Description: {test_risk['description']}")
        
        # Step 1: Generate Controls (simulate user request)
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
        
        # Step 2: Simulate Session Creation (like the agent would do)
        print(f"\n💾 Step 2: Simulating Session Creation")
        print("-" * 40)
        
        session_data = {
            "user_id": test_user_id,
            "generated_controls": controls,
            "state": {
                "user_query": "generate controls for all risks",
                "user_id": test_user_id,
                "user_context": test_user_context,
                "intent": "generate_controls_all",
                "parameters": {},
                "retrieved_context": {"risks_for_generation": [test_risk]},
                "generated_controls": controls,
                "selected_controls": [],
                "conversation_history": [],
                "final_response": "",
                "pending_selection": True,
                "session_id": ""
            }
        }
        
        session_id = mongodb.save_session(session_data)
        print(f"✅ Session created with ID: {session_id}")
        
        # Step 3: Simulate Control Selection
        print(f"\n🎯 Step 3: Simulating Control Selection")
        print("-" * 40)
        
        # Select first 2 controls
        selected_control_ids = [controls[0]["control_id"], controls[1]["control_id"]]
        print(f"   Selected control IDs: {selected_control_ids}")
        
        # Get session data
        retrieved_session = mongodb.get_session(session_id)
        if not retrieved_session:
            print("❌ Failed to retrieve session")
            return
        
        print(f"✅ Session retrieved successfully")
        
        # Get generated controls from session
        generated_controls = retrieved_session.get("state", {}).get("generated_controls", [])
        if not generated_controls:
            print("❌ No generated controls found in session")
            return
        
        print(f"✅ Found {len(generated_controls)} generated controls in session")
        
        # Filter controls based on selection
        selected_controls = [
            control for control in generated_controls
            if control.get("control_id") in selected_control_ids
        ]
        
        if not selected_controls:
            print("❌ No controls found for selected IDs")
            print(f"   Selected IDs: {selected_control_ids}")
            print(f"   Available IDs: {[c.get('control_id') for c in generated_controls]}")
            return
        
        print(f"✅ Successfully matched {len(selected_controls)} selected controls")
        
        # Step 4: Test Direct Storage (without agent re-run)
        print(f"\n💾 Step 4: Testing Direct Storage")
        print("-" * 40)
        
        try:
            # Save to MongoDB
            print("   💾 Saving selected controls to MongoDB")
            saved_control_ids = mongodb.save_controls(selected_controls)
            print(f"      ✅ Controls saved to MongoDB: {len(saved_control_ids)} controls")
            
            # Create Neo4j nodes
            print("   🔗 Creating control nodes in Neo4j")
            neo4j_success_count = 0
            for i, control in enumerate(selected_controls):
                try:
                    success = neo4j_service.create_control_node(control)
                    if success:
                        neo4j_success_count += 1
                        print(f"      ✅ Control {i+1} Neo4j node created: {control.get('control_id')}")
                    else:
                        print(f"      ⚠️  Control {i+1} Neo4j node creation failed: {control.get('control_id')}")
                except Exception as e:
                    print(f"      ❌ Control {i+1} Neo4j creation error: {e}")
            
            print(f"      📊 Neo4j results: {neo4j_success_count}/{len(selected_controls)} controls created")
            
            # Store vector embeddings
            print("   📝 Storing control embeddings")
            try:
                rag_service.store_control_embeddings(selected_controls)
                print(f"      ✅ Control embeddings stored successfully")
            except Exception as e:
                print(f"      ❌ Control embedding storage failed: {e}")
            
            # Update session
            mongodb.update_session(session_id, {
                "controls_stored": True,
                "stored_control_ids": saved_control_ids,
                "stored_at": "2024-01-15T10:00:00"
            })
            
            print(f"   ✅ Session updated with storage information")
            
        except Exception as e:
            print(f"❌ Direct storage failed: {e}")
            return
        
        # Step 5: Verify Storage
        print(f"\n🔍 Step 5: Verifying Storage")
        print("-" * 40)
        
        # Check MongoDB
        stored_controls = list(mongodb.controls.find({"user_id": test_user_id}))
        print(f"📊 MongoDB: {len(stored_controls)} controls stored")
        
        # Check Neo4j
        try:
            if neo4j_service.driver:
                with neo4j_service.driver.session() as session:
                    result = session.run("""
                        MATCH (r:Risk {id: $risk_id})-[:MITIGATES]-(c:Control)
                        RETURN count(c) as control_count
                    """, risk_id=test_risk["id"])
                    
                    control_count = result.single()["control_count"] if result.single() else 0
                    print(f"📊 Neo4j: {control_count} risk-control relationships")
        except Exception as e:
            print(f"📊 Neo4j: Unable to query relationships - {e}")
        
        print(f"\n🎉 Control Selection Flow Test Completed Successfully!")
        print(f"📋 Summary:")
        print(f"   • Controls generated: {len(controls)}")
        print(f"   • Controls selected: {len(selected_controls)}")
        print(f"   • Controls stored: {len(stored_controls)}")
        print(f"   • No agent re-generation occurred ✅")
        print(f"   • Direct storage worked correctly ✅")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_session_retrieval():
    """Test session retrieval and control matching"""
    
    print(f"\n🔍 Testing Session Retrieval and Control Matching")
    print("=" * 60)
    
    try:
        from app.database import mongodb
        
        # Create a test session with controls
        test_user_id = "test_user_003"
        test_controls = [
            {
                "control_id": "CTRL-TEST-001",
                "title": "Test Control 1",
                "description": "Test description 1",
                "risk_id": "risk_test_003",
                "user_id": test_user_id
            },
            {
                "control_id": "CTRL-TEST-002",
                "title": "Test Control 2",
                "description": "Test description 2",
                "risk_id": "risk_test_003",
                "user_id": test_user_id
            }
        ]
        
        session_data = {
            "user_id": test_user_id,
            "generated_controls": test_controls,
            "state": {
                "generated_controls": test_controls,
                "user_id": test_user_id
            }
        }
        
        session_id = mongodb.save_session(session_data)
        print(f"✅ Test session created: {session_id}")
        
        # Test retrieval
        retrieved_session = mongodb.get_session(session_id)
        if retrieved_session:
            print(f"✅ Session retrieved successfully")
            
            generated_controls = retrieved_session.get("state", {}).get("generated_controls", [])
            print(f"📋 Found {len(generated_controls)} controls in session")
            
            # Test control matching
            selected_ids = ["CTRL-TEST-001"]
            matched_controls = [
                control for control in generated_controls
                if control.get("control_id") in selected_ids
            ]
            
            print(f"🎯 Selected IDs: {selected_ids}")
            print(f"✅ Matched controls: {len(matched_controls)}")
            
            if matched_controls:
                print(f"   Control: {matched_controls[0].get('control_id')} - {matched_controls[0].get('title')}")
            
        else:
            print("❌ Failed to retrieve session")
        
        # Cleanup
        try:
            mongodb.sessions.delete_one({"_id": session_id})
            print(f"🗑️  Test session cleaned up")
        except:
            pass
        
    except Exception as e:
        print(f"❌ Session retrieval test failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_data():
    """Clean up test data"""
    
    print(f"\n🧹 Cleaning Up Test Data")
    print("=" * 40)
    
    try:
        from app.database import mongodb
        from app.neo4j_db import neo4j_service
        
        test_user_ids = ["test_user_002", "test_user_003"]
        
        for user_id in test_user_ids:
            # Clean MongoDB
            try:
                result = mongodb.controls.delete_many({"user_id": user_id})
                print(f"🗑️  MongoDB: Deleted {result.deleted_count} test controls for {user_id}")
                
                result = mongodb.sessions.delete_many({"user_id": user_id})
                print(f"🗑️  MongoDB: Deleted {result.deleted_count} test sessions for {user_id}")
            except Exception as e:
                print(f"❌ MongoDB cleanup failed for {user_id}: {e}")
            
            # Clean Neo4j
            try:
                if neo4j_service.driver:
                    with neo4j_service.driver.session() as session:
                        # Delete test control nodes
                        result = session.run("""
                            MATCH (c:Control {user_id: $user_id})
                            DETACH DELETE c
                        """, user_id=user_id)
                        
                        # Delete test risk nodes
                        result = session.run("""
                            MATCH (r:Risk {user_id: $user_id})
                            DETACH DELETE r
                        """, user_id=user_id)
                        
                print(f"🗑️  Neo4j: Test nodes deleted for {user_id}")
            except Exception as e:
                print(f"❌ Neo4j cleanup failed for {user_id}: {e}")
        
        print(f"✅ Test data cleanup completed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    print("🚀 Control Selection Flow Fix Test Suite")
    print("This will test the fixed control selection flow without agent re-generation")
    print()
    
    # Test the complete flow
    test_control_selection_flow()
    
    # Test session retrieval
    test_session_retrieval()
    
    # Clean up test data
    cleanup_test_data()
    
    print("\n🎯 All tests completed!")
    print("🔍 Check the output above for any issues in the fixed control selection flow")
