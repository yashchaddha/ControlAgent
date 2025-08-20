#!/usr/bin/env python3
"""
Test script to test improved response generation
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_improved_response_generation():
    """Test the improved response generation methods"""
    
    print("🔍 Testing Improved Response Generation")
    print("=" * 40)
    
    try:
        from app.openai_service import openai_service
        
        print("✅ OpenAI service imported successfully")
        
        # Test query
        test_query = "risks related to natural disasters"
        print(f"\n🔍 Testing query: '{test_query}'")
        
        # Mock context data (similar to what would be retrieved)
        mock_context = {
            "similar_risks": [
                {
                    "risk_id": "risk1",
                    "description": "Supply chain disruption due to natural disasters such as typhoons in the Philippines, leading to delays in raw material procurement and production shutdowns",
                    "category": "Operational",
                    "similarity": 0.830
                },
                {
                    "risk_id": "risk2", 
                    "description": "Supply chain disruption due to geopolitical tensions impacting raw material procurement for tire production",
                    "category": "Operational",
                    "similarity": 0.785
                }
            ],
            "similar_controls": [],
            "iso_guidance": [],
            "user_risks": [],
            "search_metadata": {
                "total_risks_found": 2,
                "relevance_threshold": 0.5
            }
        }
        
        mock_user_context = {
            "organization_name": "Test Company",
            "domain": "Manufacturing"
        }
        
        print("\n📊 Testing generate_contextual_response:")
        try:
            contextual_response = openai_service.generate_contextual_response(
                test_query, mock_context, mock_user_context
            )
            print("✅ Contextual response generated successfully!")
            print(f"\n📝 Response:\n{contextual_response}")
        except Exception as e:
            print(f"❌ Contextual response failed: {e}")
        
        print("\n📊 Testing synthesize_response:")
        try:
            standard_response = openai_service.synthesize_response(
                test_query, mock_context, None
            )
            print("✅ Standard response generated successfully!")
            print(f"\n📝 Response:\n{standard_response}")
        except Exception as e:
            print(f"❌ Standard response failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Improved Response Generation Test")
    print("This will test the enhanced response generation methods")
    print()
    
    test_improved_response_generation()
    
    print("\n�� Test completed!")
