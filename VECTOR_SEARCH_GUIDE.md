# Enhanced Vector Search & Query Embedding Guide

## Overview

This guide explains the enhanced vector search capabilities implemented in the ISO 27001 Control Agent system. The system now generates vector embeddings for user queries and uses them to retrieve highly relevant data from the vector database.

## 🚀 Key Features

### 1. **Query Embedding Generation**
- **Automatic**: Every user query is automatically converted to a 1536-dimensional vector using OpenAI's `text-embedding-ada-002` model
- **Real-time**: Embeddings are generated on-the-fly for immediate search
- **Consistent**: Same query always produces the same embedding

### 2. **Enhanced Vector Search**
- **Multi-source retrieval**: Search across controls, risks, ISO guidance, and user-specific data
- **Similarity scoring**: Results ranked by cosine similarity (0.0 to 1.0)
- **Configurable thresholds**: Adjustable relevance filters
- **Hybrid search**: Combine multiple search types in one query

### 3. **Query History & Learning**
- **Query storage**: All queries and their embeddings are stored for future reference
- **Similarity matching**: Find similar previous queries to provide context
- **Continuous improvement**: System learns from user interactions

## 🔍 Search Types

### **Semantic Search** (`POST /api/v1/search/semantic`)
```json
{
  "query": "How do I implement access control for cloud services?",
  "search_type": "hybrid",  // "controls", "risks", "guidance", "hybrid"
  "limit": 10,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "query": "How do I implement access control for cloud services?",
  "query_embedding_generated": true,
  "search_type": "hybrid",
  "results": {
    "controls": [
      {
        "control_id": "ACC-001",
        "title": "Cloud Access Control",
        "similarity": 0.89
      }
    ],
    "risks": [...],
    "guidance": [...]
  },
  "search_metadata": {
    "similarity_threshold": 0.7,
    "total_vectors_in_db": {...},
    "embedding_model": "text-embedding-ada-002"
  },
  "total_results": 15
}
```

### **Query Similarity Search** (`POST /api/v1/search/query-similarity`)
Find similar previous queries to provide context and learning.

### **Enhanced Context Retrieval** (`POST /api/v1/search/enhanced-context`)
Get comprehensive context using the RAG service with vector search.

### **Vector Database Statistics** (`GET /api/v1/search/vector-stats`)
Monitor the health and size of your vector database.

## 🏗️ Architecture

```
User Query → OpenAI Embedding → Vector Search → Context Retrieval → Response Generation
     ↓              ↓              ↓              ↓              ↓
  "How to..." → [0.1, 0.3, ...] → Similar → Enhanced → AI Response
                                    Results   Context
```

### **Database Schema**

#### **Query Embeddings Table**
```sql
CREATE TABLE query_embeddings (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(255) UNIQUE,
    user_id VARCHAR(255),
    query_text TEXT,
    intent VARCHAR(100),
    response_context JSONB,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Vector Indexes**
```sql
-- Efficient similarity search using pgvector
CREATE INDEX query_embedding_idx ON query_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## 💡 Usage Examples

### **1. Basic Semantic Search**
```python
import requests

response = requests.post("http://localhost:8000/api/v1/search/semantic", json={
    "query": "What are the best practices for incident response?",
    "search_type": "hybrid",
    "limit": 5,
    "similarity_threshold": 0.8
})

results = response.json()
print(f"Found {results['total_results']} relevant results")
```

### **2. Finding Similar Queries**
```python
response = requests.post("http://localhost:8000/api/v1/search/query-similarity", json={
    "query": "How to handle data breaches?",
    "limit": 3,
    "similarity_threshold": 0.6
})

similar_queries = response.json()
for query in similar_queries['similar_queries']:
    print(f"Similarity: {query['similarity']:.3f} - {query['query_text']}")
```

### **3. Enhanced Context Retrieval**
```python
response = requests.post("http://localhost:8000/api/v1/search/enhanced-context", json={
    "query": "What controls do I need for GDPR compliance?",
    "limit": 10
})

context = response.json()
print(f"Retrieved context with {len(context['context']['similar_controls'])} controls")
```

## 🔧 Configuration

### **Environment Variables**
```bash
# OpenAI API for embeddings
OPENAI_API_KEY=your_openai_api_key_here

# Vector database (PostgreSQL + pgvector)
POSTGRES_URI=postgresql://user:pass@localhost:5432/dbname

# Embedding model configuration
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_DIMENSIONS=1536
```

### **Similarity Thresholds**
- **0.9+**: Very high relevance (exact matches)
- **0.8-0.9**: High relevance (strong matches)
- **0.7-0.8**: Good relevance (moderate matches)
- **0.6-0.7**: Acceptable relevance (weak matches)
- **<0.6**: Low relevance (consider filtering out)

## 🧪 Testing

### **Run the Test Script**
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python test_vector_search.py
```

### **Test Individual Components**
```python
# Test embedding generation
from app.openai_service import openai_service
embedding = openai_service.get_embedding("Test query")
print(f"Embedding dimensions: {len(embedding)}")

# Test vector search
from app.postgres import postgres_service
stats = postgres_service.get_search_statistics()
print(f"Database stats: {stats}")
```

## 📊 Monitoring & Analytics

### **Vector Database Health**
- **Record counts**: Monitor growth of embeddings
- **Index performance**: Track search response times
- **Storage usage**: Monitor vector storage consumption

### **Search Quality Metrics**
- **Query success rate**: Percentage of queries with results
- **Average similarity scores**: Overall relevance quality
- **User satisfaction**: Track query refinement patterns

## 🚀 Performance Optimization

### **1. Index Tuning**
```sql
-- Adjust IVF lists for your data size
CREATE INDEX control_embedding_idx ON control_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 200);
```

### **2. Batch Operations**
```python
# Store multiple embeddings efficiently
def store_batch_embeddings(controls):
    for control in controls:
        rag_service.store_control_embedding(control)
```

### **3. Caching**
- **Query embeddings**: Cache frequently used embeddings
- **Search results**: Cache common search patterns
- **User context**: Cache user-specific data

## 🔒 Security Considerations

### **Data Privacy**
- **User isolation**: Queries are scoped to authenticated users
- **Embedding storage**: Secure storage of vector representations
- **Access control**: Role-based permissions for search operations

### **API Security**
- **Rate limiting**: Prevent abuse of embedding generation
- **Input validation**: Sanitize user queries
- **Audit logging**: Track all search operations

## 🎯 Best Practices

### **1. Query Formulation**
- **Be specific**: "How to implement MFA for admin accounts?" vs "MFA"
- **Use context**: Include relevant domain or technology details
- **Natural language**: Write queries as you would ask a colleague

### **2. Threshold Tuning**
- **Start high**: Begin with 0.8+ for precision
- **Adjust down**: Lower to 0.6+ for recall
- **Monitor results**: Track user satisfaction with different thresholds

### **3. Regular Maintenance**
- **Clean old queries**: Archive or delete outdated embeddings
- **Update indexes**: Rebuild indexes after major data changes
- **Monitor performance**: Track search response times

## 🐛 Troubleshooting

### **Common Issues**

#### **1. No Results Found**
```bash
# Check database connectivity
curl http://localhost:8000/api/v1/search/vector-stats

# Verify embeddings exist
SELECT COUNT(*) FROM control_embeddings;
```

#### **2. Low Similarity Scores**
```bash
# Lower threshold temporarily
"similarity_threshold": 0.5

# Check embedding quality
# Ensure consistent text preprocessing
```

#### **3. Slow Search Performance**
```bash
# Check index health
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;

# Consider index optimization
REINDEX INDEX control_embedding_idx;
```

### **Debug Mode**
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check embedding generation
embedding = openai_service.get_embedding("debug query")
print(f"Embedding: {embedding[:5]}...")
```

## 🔮 Future Enhancements

### **Planned Features**
- **Multi-modal embeddings**: Support for images and documents
- **Semantic clustering**: Group similar queries automatically
- **Learning feedback**: Improve embeddings based on user actions
- **Real-time updates**: Live embedding updates for new content

### **Advanced Search**
- **Fuzzy matching**: Handle typos and variations
- **Semantic expansion**: Automatically expand queries with synonyms
- **Contextual search**: Consider conversation history
- **Personalization**: Learn user preferences over time

## 📚 Additional Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Vector Similarity Search](https://en.wikipedia.org/wiki/Vector_similarity_search)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)

---

This enhanced vector search system transforms your chatbot from simple keyword matching to intelligent, context-aware responses that learn and improve over time.
