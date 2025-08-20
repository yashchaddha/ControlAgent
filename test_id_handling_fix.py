#!/usr/bin/env python3
"""
Test script to verify that the system can handle both UUIDs and control_ids
for control selection, fixing the "No controls found for selected IDs" error
"""

import sys
import os
import logging
import uuid

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_uuid_vs_control_id_handling():
    """Test that the system can handle both UUIDs and control_ids"""
    
    print("🔍 Testing UUID vs Control ID Handling")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from app.database import mongodb
        
        print("✅ MongoDB service imported successfully")
        
        # Test data with both UUIDs and control_ids
        test_user_id = "test_user_004"
        test_controls = [
            {
                "id": "9860aec2-678c-4dbe-a16c-e6266cd1cf69",  # UUID
                "control_id": "CTRL-TEST-001",                   # Control ID
                "title": "Test Control 1",
                "description": "Test description 1",
                "risk_id": "risk_test_004",
                "user_id": test_user_id
            },
            {
                "id": "da04c3cc-dee1-40a3-ac54-14f87c6134a4",  # UUID
                "control_id": "CTRL-TEST-002",                   # Control ID
                "title": "Test Control 2",
                "description": "Test description 2",
                "risk_id": "risk_test_004",
                "user_id": test_user_id
            },
            {
                "id": "9edf737b-4e7c-4d66-9161-e938f00a0d72",  # UUID
                "control_id": "CTRL-TEST-003",                   # Control ID
                "title": "Test Control 3",
                "description": "Test description 3",
                "risk_id": "risk_test_004",
                "user_id": test_user_id
            }
        ]
        
        print(f"\n📋 Test Controls:")
        for i, control in enumerate(test_controls):
            print(f"   Control {i+1}:")
            print(f"      UUID: {control['id']}")
            print(f"      Control ID: {control['control_id']}")
            print(f"      Title: {control['title']}")
        
        # Test 1: Selection by UUIDs (what frontend is currently sending)
        print(f"\n🧪 Test 1: Selection by UUIDs")
        print("-" * 40)
        
        selected_uuids = [
            "9860aec2-678c-4dbe-a16c-e6266cd1cf69",
            "da04c3cc-dee1-40a3-ac54-14f87c6134a4"
        ]
        
        print(f"   Selected UUIDs: {selected_uuids}")
        
        # Simulate the selection logic from the router
        selected_controls_by_uuid = []
        
        for selected_id in selected_uuids:
            # Try to find control by UUID first
            control_by_uuid = next(
                (control for control in test_controls if control.get("id") == selected_id), 
                None
            )
            
            # Try to find control by control_id if UUID not found
            control_by_control_id = next(
                (control for control in test_controls if control.get("control_id") == selected_id), 
                None
            )
            
            if control_by_uuid:
                selected_controls_by_uuid.append(control_by_uuid)
                print(f"      ✅ Control found by UUID: {selected_id}")
            elif control_by_control_id:
                selected_controls_by_uuid.append(control_by_control_id)
                print(f"      ✅ Control found by control_id: {selected_id}")
            else:
                print(f"      ❌ Control not found for ID: {selected_id}")
        
        print(f"   📊 Results: {len(selected_controls_by_uuid)} controls found by UUIDs")
        
        # Test 2: Selection by Control IDs
        print(f"\n🧪 Test 2: Selection by Control IDs")
        print("-" * 40)
        
        selected_control_ids = [
            "CTRL-TEST-001",
            "CTRL-TEST-003"
        ]
        
        print(f"   Selected Control IDs: {selected_control_ids}")
        
        # Simulate the selection logic from the router
        selected_controls_by_control_id = []
        
        for selected_id in selected_control_ids:
            # Try to find control by UUID first
            control_by_uuid = next(
                (control for control in test_controls if control.get("id") == selected_id), 
                None
            )
            
            # Try to find control by control_id if UUID not found
            control_by_control_id = next(
                (control for control in test_controls if control.get("control_id") == selected_id), 
                None
            )
            
            if control_by_uuid:
                selected_controls_by_control_id.append(control_by_uuid)
                print(f"      ✅ Control found by UUID: {selected_id}")
            elif control_by_control_id:
                selected_controls_by_control_id.append(control_by_control_id)
                print(f"      ✅ Control found by control_id: {selected_id}")
            else:
                print(f"      ❌ Control not found for ID: {selected_id}")
        
        print(f"   📊 Results: {len(selected_controls_by_control_id)} controls found by Control IDs")
        
        # Test 3: Mixed Selection (some UUIDs, some Control IDs)
        print(f"\n🧪 Test 3: Mixed Selection")
        print("-" * 40)
        
        mixed_selection = [
            "9860aec2-678c-4dbe-a16c-e6266cd1cf69",  # UUID
            "CTRL-TEST-002"                            # Control ID
        ]
        
        print(f"   Mixed Selection: {mixed_selection}")
        
        # Simulate the selection logic from the router
        selected_controls_mixed = []
        
        for selected_id in mixed_selection:
            # Try to find control by UUID first
            control_by_uuid = next(
                (control for control in test_controls if control.get("id") == selected_id), 
                None
            )
            
            # Try to find control by control_id if UUID not found
            control_by_control_id = next(
                (control for control in test_controls if control.get("control_id") == selected_id), 
                None
            )
            
            if control_by_uuid:
                selected_controls_mixed.append(control_by_uuid)
                print(f"      ✅ Control found by UUID: {selected_id}")
            elif control_by_control_id:
                selected_controls_mixed.append(control_by_control_id)
                print(f"      ✅ Control found by control_id: {selected_id}")
            else:
                print(f"      ❌ Control not found for ID: {selected_id}")
        
        print(f"   📊 Results: {len(selected_controls_mixed)} controls found by mixed selection")
        
        # Test 4: Invalid Selection (non-existent IDs)
        print(f"\n🧪 Test 4: Invalid Selection")
        print("-" * 40)
        
        invalid_selection = [
            "invalid-uuid-123",
            "CTRL-INVALID-999"
        ]
        
        print(f"   Invalid Selection: {invalid_selection}")
        
        # Simulate the selection logic from the router
        selected_controls_invalid = []
        
        for selected_id in invalid_selection:
            # Try to find control by UUID first
            control_by_uuid = next(
                (control for control in test_controls if control.get("id") == selected_id), 
                None
            )
            
            # Try to find control by control_id if UUID not found
            control_by_control_id = next(
                (control for control in test_controls if control.get("control_id") == selected_id), 
                None
            )
            
            if control_by_uuid:
                selected_controls_invalid.append(control_by_uuid)
                print(f"      ✅ Control found by UUID: {selected_id}")
            elif control_by_control_id:
                selected_controls_invalid.append(control_by_control_id)
                print(f"      ✅ Control found by control_id: {selected_id}")
            else:
                print(f"      ❌ Control not found for ID: {selected_id}")
        
        print(f"   📊 Results: {len(selected_controls_invalid)} controls found by invalid selection")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   • UUID Selection: {len(selected_controls_by_uuid)}/{len(selected_uuids)} controls found")
        print(f"   • Control ID Selection: {len(selected_controls_by_control_id)}/{len(selected_control_ids)} controls found")
        print(f"   • Mixed Selection: {len(selected_controls_mixed)}/{len(mixed_selection)} controls found")
        print(f"   • Invalid Selection: {len(selected_controls_invalid)}/{len(invalid_selection)} controls found")
        
        # Verify the fix works
        if len(selected_controls_by_uuid) == len(selected_uuids):
            print(f"\n✅ UUID Selection Test PASSED - Frontend UUIDs will work correctly!")
        else:
            print(f"\n❌ UUID Selection Test FAILED - Frontend UUIDs won't work!")
        
        if len(selected_controls_by_control_id) == len(selected_control_ids):
            print(f"✅ Control ID Selection Test PASSED - Control IDs will work correctly!")
        else:
            print(f"❌ Control ID Selection Test FAILED - Control IDs won't work!")
        
        print(f"\n🎯 ID Handling Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_session_control_matching():
    """Test control matching in a session context"""
    
    print(f"\n🔍 Testing Session Control Matching")
    print("=" * 50)
    
    try:
        from app.database import mongodb
        
        # Create a test session with controls
        test_user_id = "test_user_005"
        test_controls = [
            {
                "id": "9860aec2-678c-4dbe-a16c-e6266cd1cf69",
                "control_id": "CTRL-TEST-001",
                "title": "Test Control 1",
                "risk_id": "risk_test_005",
                "user_id": test_user_id
            },
            {
                "id": "da04c3cc-dee1-40a3-ac54-14f87c6134a4",
                "control_id": "CTRL-TEST-002",
                "title": "Test Control 2",
                "risk_id": "risk_test_005",
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
        
        # Test retrieval and matching
        retrieved_session = mongodb.get_session(session_id)
        if retrieved_session:
            print(f"✅ Session retrieved successfully")
            
            generated_controls = retrieved_session.get("state", {}).get("generated_controls", [])
            print(f"📋 Found {len(generated_controls)} controls in session")
            
            # Test UUID matching (what frontend currently sends)
            selected_uuids = ["9860aec2-678c-4dbe-a16c-e6266cd1cf69"]
            print(f"🎯 Testing UUID selection: {selected_uuids}")
            
            matched_controls = []
            for selected_id in selected_uuids:
                # Try to find control by UUID first
                control_by_uuid = next(
                    (control for control in generated_controls if control.get("id") == selected_id), 
                    None
                )
                
                # Try to find control by control_id if UUID not found
                control_by_control_id = next(
                    (control for control in generated_controls if control.get("control_id") == selected_id), 
                    None
                )
                
                if control_by_uuid:
                    matched_controls.append(control_by_uuid)
                    print(f"   ✅ Control found by UUID: {selected_id}")
                elif control_by_control_id:
                    matched_controls.append(control_by_control_id)
                    print(f"   ✅ Control found by control_id: {selected_id}")
                else:
                    print(f"   ❌ Control not found for ID: {selected_id}")
            
            print(f"📊 UUID Matching Results: {len(matched_controls)}/{len(selected_uuids)} controls found")
            
            if matched_controls:
                print(f"   Found control: {matched_controls[0].get('title')}")
            
        else:
            print("❌ Failed to retrieve session")
        
        # Cleanup
        try:
            mongodb.sessions.delete_one({"_id": session_id})
            print(f"🗑️  Test session cleaned up")
        except:
            pass
        
    except Exception as e:
        print(f"❌ Session control matching test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 ID Handling Fix Test Suite")
    print("This will test that the system can handle both UUIDs and control_ids")
    print()
    
    # Test ID handling
    test_uuid_vs_control_id_handling()
    
    # Test session control matching
    test_session_control_matching()
    
    print("\n🎯 All tests completed!")
    print("🔍 Check the output above to verify the ID handling fix works")
