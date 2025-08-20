#!/usr/bin/env python3
"""
Demo script for enhanced chatbot with vector search capabilities
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def demo_enhanced_chatbot():
    """Demonstrate the enhanced chatbot capabilities"""
    
    print("🤖 Enhanced Chatbot Demo with Vector Search")
    print("=" * 50)
    
    try:
        # Import the enhanced agent
        from langgraph_agent import iso_agent
        
        print("✅ Enhanced agent imported successfully")
        
        # Demo queries to showcase different capabilities
        demo_queries = [
            "How do I implement access control for cloud services?",
            "What are the best practices for incident response?",
            "How to handle data breaches in financial services?",
            "What controls do I need for GDPR compliance?",
            "How to secure API endpoints?",
            "What are the requirements for backup and recovery?"
        ]
        
        print(f"\n📝 Running {len(demo_queries)} demo queries...")
        print("This will demonstrate:")
        print("  • Query embedding generation")
        print("  • Vector search across multiple sources")
        print("  • Context-aware response generation")
        print("  • Query embedding storage for learning")
        print()
        
        for i, query in enumerate(demo_queries, 1):
            print(f"🔍 Query {i}: {query}")
            print("-" * 40)
            
            try:
                # Run the query through the enhanced agent
                result = await iso_agent.run(query, "demo_user")
                
                print(f"✅ Response generated successfully")
                print(f"📊 Intent classified: {result.get('intent', 'Unknown')}")
                print(f"🔍 Context retrieved: {len(result.get('retrieved_context', {}).get('similar_controls', []))} controls, {len(result.get('retrieved_context', {}).get('similar_risks', []))} risks")
                
                if result.get('generated_controls'):
                    print(f"🎯 Controls generated: {len(result['generated_controls'])}")
                
                print(f"💬 Response: {result.get('final_response', 'No response')[:100]}...")
                print()
                
                # Small delay between queries
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
                print()
        
        print("🎉 Demo completed successfully!")
        print("\n📚 What happened behind the scenes:")
        print("1. Each query was converted to a 1536-dimensional vector")
        print("2. Vector similarity search found relevant controls, risks, and guidance")
        print("3. Context was retrieved from multiple sources (vector DB, knowledge graph)")
        print("4. AI generated contextual responses using the retrieved information")
        print("5. Query embeddings were stored for future learning")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        print("and have activated the virtual environment")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

def demo_vector_search_only():
    """Demo just the vector search capabilities without the full agent"""
    
    print("🔍 Vector Search Only Demo")
    print("=" * 30)
    
    try:
        from rag_service import rag_service
        from openai_service import openai_service
        
        print("✅ Services imported successfully")
        
        # Test query
        test_query = "How to implement multi-factor authentication?"
        print(f"\n🔍 Test query: {test_query}")
        
        # Generate embedding
        embedding = openai_service.get_embedding(test_query)
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
        
        # Retrieve context
        context = rag_service.retrieve_context_for_query(
            test_query, 
            "query_controls", 
            {}, 
            "demo_user"
        )
        
        print(f"✅ Context retrieved:")
        print(f"   • Controls: {len(context.get('similar_controls', []))}")
        print(f"   • Risks: {len(context.get('similar_risks', []))}")
        print(f"   • Guidance: {len(context.get('iso_guidance', []))}")
        print(f"   • User risks: {len(context.get('user_risks', []))}")
        
        # Show search metadata
        metadata = context.get('search_metadata', {})
        print(f"📊 Search metadata:")
        print(f"   • Total controls found: {metadata.get('total_controls_found', 0)}")
        print(f"   • Total risks found: {metadata.get('total_risks_found', 0)}")
        print(f"   • Relevance threshold: {metadata.get('relevance_threshold', 0)}")
        
        print("\n🎉 Vector search demo completed!")
        
    except Exception as e:
        print(f"❌ Vector search demo failed: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced Chatbot Demo")
    print("Choose demo type:")
    print("1. Full enhanced chatbot demo")
    print("2. Vector search only demo")
    print("3. Both")
    print()
    
    try:
        choice = input("Enter choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            asyncio.run(demo_enhanced_chatbot())
        elif choice == "2":
            demo_vector_search_only()
        elif choice == "3":
            print("\n" + "="*50)
            demo_vector_search_only()
            print("\n" + "="*50)
            asyncio.run(demo_enhanced_chatbot())
        else:
            print("Invalid choice. Running both demos...")
            print("\n" + "="*50)
            demo_vector_search_only()
            print("\n" + "="*50)
            asyncio.run(demo_enhanced_chatbot())
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure you have:")
        print("1. Activated the virtual environment")
        print("2. Set up your .env file with database credentials")
        print("3. Started the required database services")
