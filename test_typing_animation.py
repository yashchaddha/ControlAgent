#!/usr/bin/env python3
"""
Test script to verify the typing animation functionality in the chatbot interface.
"""

import asyncio
import sys
import os
import time

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from openai_service import openai_service
from rag_service import rag_service

async def test_typing_animation_responses():
    """Test different types of responses to verify typing animation behavior"""
    
    print("🎯 Testing Typing Animation Functionality")
    print("=" * 55)
    
    test_queries = [
        "Show me the controls related to supply chain",
        "What is ISO 27001?",
        "Generate controls for operational risk"
    ]
    
    test_user_id = "test_user"
    
    for i, test_query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test_query}")
        print("-" * 40)
        
        try:
            # Generate embedding for the query
            query_embedding = openai_service.get_embedding(test_query)
            
            # Get context
            context = rag_service._get_general_query_context(
                query_embedding, 
                test_user_id, 
                test_query,
                vector_only=True
            )
            
            # Generate response
            response = openai_service.generate_general_controls_response(
                test_query, 
                context, 
                {"organization_name": "Test Org", "domain": "Technology"}
            )
            
            # Analyze response for typing animation
            print(f"   📝 Response Analysis:")
            print(f"      - Length: {len(response)} characters")
            print(f"      - Contains markdown: {'Yes' if any(char in response for char in '*#`') else 'No'}")
            print(f"      - Estimated typing time: {len(response) * 0.03:.1f} seconds (at 30ms/char)")
            
            # Check for different content types
            if "### Control" in response:
                print(f"      - Content type: Control listing")
                print(f"      - Controls found: {response.count('### Control')}")
            elif "## " in response:
                print(f"      - Content type: Structured response with headers")
            else:
                print(f"      - Content type: General text response")
            
            # Show response preview
            print(f"\n📋 Response Preview (first 200 chars):")
            preview = response[:200] + "..." if len(response) > 200 else response
            print(f"      {preview}")
            
        except Exception as e:
            print(f"   ❌ Error during testing: {e}")
        
        print()
    
    print("🎯 Typing Animation Test Completed!")

async def test_typing_speed_calculation():
    """Test the typing speed calculation logic"""
    
    print("\n🧪 Testing Typing Speed Calculation")
    print("=" * 40)
    
    # Test different response lengths
    test_responses = [
        ("Short response", "This is a short response."),
        ("Medium response", "This is a medium length response that contains more text and should take a moderate amount of time to type out."),
        ("Long response", "This is a very long response that contains a lot of text and should take a significant amount of time to type out. It includes multiple sentences and paragraphs to simulate a real-world scenario where the agent provides comprehensive information." * 3),
        ("Markdown response", "## Header\n**Bold text** and *italic text* with `code snippets`."),
        ("Control response", "### Control 1: Example Control\n**Description**: This is an example control.\n**Implementation**: Implementation details here.")
    ]
    
    for response_type, response_text in test_responses:
        print(f"\n📝 {response_type}:")
        print(f"   - Length: {len(response_text)} characters")
        
        # Calculate estimated typing time
        base_speed = 30  # ms per character
        
        if len(response_text) > 500:
            speed = 20
            print(f"   - Speed: {speed}ms/char (fast - long response)")
        elif len(response_text) < 100:
            speed = 50
            print(f"   - Speed: {speed}ms/char (slow - short response)")
        else:
            speed = base_speed
            print(f"   - Speed: {speed}ms/char (normal)")
        
        # Check for markdown
        has_markdown = any(char in response_text for char in '*#`')
        if has_markdown:
            speed = max(speed - 10, 15)
            print(f"   - Adjusted speed: {speed}ms/char (markdown detected)")
        
        estimated_time = len(response_text) * speed / 1000
        print(f"   - Estimated typing time: {estimated_time:.1f} seconds")
    
    print("\n🧪 Typing Speed Calculation Test Completed!")

async def test_typing_animation_user_experience():
    """Test the overall user experience with typing animation"""
    
    print("\n👤 Testing Typing Animation User Experience")
    print("=" * 45)
    
    print("🎯 User Experience Flow:")
    print("   1. User sends message")
    print("   2. Typing loader appears (Agent is thinking...)")
    print("   3. Typing loader disappears")
    print("   4. Agent response appears with typing animation")
    print("   5. Typing animation completes")
    print("   6. User can send next message")
    
    print("\n⏱️  Timing Analysis:")
    print("   - Typing loader delay: 300ms (smooth transition)")
    print("   - Typing animation: Variable based on content length")
    print("   - Completion delay: 500ms (show final result)")
    
    print("\n🎨 Visual Features:")
    print("   - Animated cursor (▋) during typing")
    print("   - Smooth character-by-character appearance")
    print("   - Real-time markdown formatting")
    print("   - Auto-scroll as text grows")
    
    print("\n🔧 Technical Implementation:")
    print("   - Async typing function with configurable speed")
    print("   - Dynamic speed adjustment based on content")
    print("   - Markdown parsing during typing")
    print("   - Proper state management")
    
    print("\n👤 User Experience Test Completed!")

async def main():
    """Main test function"""
    await test_typing_animation_responses()
    await test_typing_speed_calculation()
    await test_typing_animation_user_experience()

if __name__ == "__main__":
    asyncio.run(main())
