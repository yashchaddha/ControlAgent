#!/usr/bin/env python3
"""
Test script to verify control generation fixes
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import after adding to path
from langgraph_agent import ISO27001Agent

async def test_control_generation():
    """Test the control generation workflow"""
    print("🧪 Testing Control Generation Fixes")
    print("=" * 50)
    
    try:
        # Initialize the agent
        print("🔧 Initializing ISO27001Agent...")
        agent = ISO27001Agent()
        print("   ✅ Agent initialized successfully")
        
        # Test user query
        user_query = "Generate controls for all risks"
        user_id = "yash"
        
        print(f"\n📝 Testing query: '{user_query}'")
        print(f"👤 User ID: {user_id}")
        
        # Run the workflow
        print("\n🚀 Running workflow...")
        result = await agent.run(user_query, user_id)
        
        print("\n📊 Workflow Results:")
        print(f"   Final Response: {result.get('final_response', 'No response')[:200]}...")
        print(f"   Generated Controls: {len(result.get('generated_controls', []))}")
        print(f"   Pending Selection: {result.get('pending_selection', False)}")
        print(f"   Session ID: {result.get('session_id', 'None')}")
        
        if result.get('generated_controls'):
            print(f"\n🎯 Generated Controls Details:")
            for i, control in enumerate(result['generated_controls'][:3]):  # Show first 3
                print(f"   Control {i+1}:")
                print(f"      ID: {control.get('id', 'N/A')}")
                print(f"      Control ID: {control.get('control_id', 'N/A')}")
                print(f"      Title: {control.get('title', 'N/A')[:50]}...")
                print(f"      Risk ID: {control.get('risk_id', 'N/A')}")
                print(f"      User ID: {control.get('user_id', 'N/A')}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_control_generation())
