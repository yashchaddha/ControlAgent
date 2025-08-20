#!/usr/bin/env python3
"""
Test script to verify control generation works correctly with all required fields
"""

import sys
import os
import logging

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_control_generation():
    """Test control generation with proper field validation"""
    
    print("🔧 Testing Control Generation with Field Validation")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from app.openai_service import openai_service
        from app.models import Control
        
        print("✅ OpenAI service imported successfully")
        
        # Test data
        test_risk = {
            "id": "risk_test_001",
            "description": "Supply chain disruption due to natural disasters",
            "category": "Operational Risk",
            "impact": "High",
            "likelihood": "Medium"
        }
        
        test_user_context = {
            "organization_name": "Test Corp",
            "domain": "Manufacturing",
            "location": "Philippines"
        }
        
        print(f"\n📋 Test Risk:")
        print(f"   ID: {test_risk['id']}")
        print(f"   Description: {test_risk['description']}")
        print(f"   Category: {test_risk['category']}")
        
        print(f"\n👤 Test User Context:")
        print(f"   Organization: {test_user_context['organization_name']}")
        print(f"   Domain: {test_user_context['domain']}")
        print(f"   Location: {test_user_context['location']}")
        
        # Generate controls
        print(f"\n🔧 Generating controls...")
        controls = openai_service.generate_controls(test_risk, test_user_context)
        
        if not controls:
            print("❌ No controls generated!")
            return
        
        print(f"✅ Generated {len(controls)} controls")
        
        # Validate each control
        print(f"\n🔍 Validating generated controls:")
        valid_controls = []
        
        for i, control in enumerate(controls):
            print(f"\n   Control {i+1}:")
            print(f"      Title: {control.get('title', 'Missing!')[:50]}...")
            print(f"      Control ID: {control.get('control_id', 'Missing!')}")
            print(f"      Description: {control.get('description', 'Missing!')[:50]}...")
            print(f"      Domain Category: {control.get('domain_category', 'Missing!')}")
            print(f"      Annex Reference: {control.get('annex_reference', 'Missing!')}")
            print(f"      Control Statement: {control.get('control_statement', 'Missing!')[:50]}...")
            print(f"      Implementation Guidance: {control.get('implementation_guidance', 'Missing!')[:50]}...")
            
            # Check required fields
            required_fields = ["control_id", "title", "description", "domain_category", 
                             "annex_reference", "control_statement", "implementation_guidance"]
            
            missing_fields = [field for field in required_fields if not control.get(field)]
            
            if missing_fields:
                print(f"      ❌ Missing required fields: {missing_fields}")
            else:
                print(f"      ✅ All required fields present")
                valid_controls.append(control)
        
        print(f"\n📊 Validation Results:")
        print(f"   Total controls: {len(controls)}")
        print(f"   Valid controls: {len(valid_controls)}")
        print(f"   Invalid controls: {len(controls) - len(valid_controls)}")
        
        # Test Pydantic model validation
        if valid_controls:
            print(f"\n🧪 Testing Pydantic model validation:")
            
            for i, control_data in enumerate(valid_controls):
                try:
                    # Add required fields that the model expects
                    control_data["risk_id"] = test_risk["id"]
                    control_data["user_id"] = "test_user"
                    
                    # Try to create Control model instance
                    control_instance = Control(**control_data)
                    print(f"   ✅ Control {i+1} validates successfully with Pydantic")
                    
                except Exception as e:
                    print(f"   ❌ Control {i+1} Pydantic validation failed: {e}")
        
        print(f"\n🎯 Control generation test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_control_validation():
    """Test the control validation logic"""
    
    print(f"\n🔍 Testing Control Validation Logic")
    print("=" * 50)
    
    try:
        # Mock generated controls (similar to what the agent would produce)
        mock_controls = [
            {
                "control_id": "CTRL-001",
                "title": "Test Control 1",
                "description": "Test description 1",
                "domain_category": "Organizational",
                "annex_reference": "A.5.1",
                "control_statement": "Test statement 1",
                "implementation_guidance": "Test guidance 1",
                "risk_id": "risk_001",
                "user_id": "test_user"
            },
            {
                "control_id": "CTRL-002",
                "title": "Test Control 2",
                "description": "Test description 2",
                "domain_category": "Technical",
                "annex_reference": "A.8.1",
                "control_statement": "Test statement 2",
                "implementation_guidance": "Test guidance 2",
                "risk_id": "risk_002",
                "user_id": "test_user"
            }
        ]
        
        print(f"📋 Testing validation with {len(mock_controls)} mock controls")
        
        # Simulate the validation logic from the router
        validated_controls = []
        
        for i, control in enumerate(mock_controls):
            try:
                # Ensure all required fields are present
                validated_control = {
                    "id": control.get("id"),
                    "control_id": control.get("control_id"),
                    "title": control.get("title"),
                    "description": control.get("description"),
                    "domain_category": control.get("domain_category"),
                    "annex_reference": control.get("annex_reference"),
                    "control_statement": control.get("control_statement"),
                    "implementation_guidance": control.get("implementation_guidance"),
                    "risk_id": control.get("risk_id"),
                    "user_id": control.get("user_id"),
                    "created_at": control.get("created_at")
                }
                
                # Validate that required fields are present
                required_fields = ["control_id", "title", "description", "domain_category", 
                                "annex_reference", "control_statement", "implementation_guidance", 
                                "risk_id", "user_id"]
                
                missing_fields = [field for field in required_fields if not validated_control.get(field)]
                
                if missing_fields:
                    print(f"   ⚠️  Control {i+1} missing required fields: {missing_fields}")
                    continue
                
                validated_controls.append(validated_control)
                print(f"   ✅ Control {i+1} validated successfully")
                
            except Exception as e:
                print(f"   ❌ Control {i+1} validation failed: {e}")
                continue
        
        print(f"\n📊 Validation Results:")
        print(f"   Total controls: {len(mock_controls)}")
        print(f"   Valid controls: {len(validated_controls)}")
        
        # Test Pydantic model creation
        if validated_controls:
            print(f"\n🧪 Testing Pydantic model creation:")
            
            from app.models import Control
            
            for i, control_data in enumerate(validated_controls):
                try:
                    control_instance = Control(**control_data)
                    print(f"   ✅ Control {i+1} creates Pydantic model successfully")
                    
                except Exception as e:
                    print(f"   ❌ Control {i+1} Pydantic model creation failed: {e}")
        
        print(f"\n🎯 Control validation test completed!")
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Control Generation and Validation Test")
    print("This will test if controls are generated with all required fields")
    print()
    
    # Test control generation
    test_control_generation()
    
    # Test validation logic
    test_control_validation()
    
    print("\n🎯 All tests completed!")
    print("🔍 Check the output above for any validation issues")
