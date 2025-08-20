# ISO 27001 Control Agent Implementation Guide

## Architecture Overview

The system implements a LangGraph agent with agentic RAG and knowledge graph capabilities for ISO 27001:2022 control generation.

### Core Components

1. **LangGraph Agent** (`langgraph_agent.py`)

   - Orchestrates the entire workflow with conditional routing
   - Handles intent classification, context retrieval, control generation, user interaction, and data storage

2. **Agentic RAG** (`rag_service.py`)

   - Vector similarity search using PostgreSQL + pgvector
   - Context retrieval from multiple sources
   - Embedding storage and management

3. **Knowledge Graph** (`neo4j_db.py`)

   - Neo4j for storing relationships between users, risks, controls, and annexes
   - Complex query capabilities for cross-user insights
   - Graph traversal for intelligent recommendations

4. **Data Storage** (`database.py`)
   - MongoDB for primary data storage (users, risks, controls)
   - Dual storage pattern for optimal performance

## Workflow

### Control Generation Flow

1. **User Query**: "Generate controls for my financial risks"
2. **Intent Classification**: LLM determines intent and extracts parameters
3. **Context Retrieval**:
   - Vector search for similar risks/controls
   - Graph traversal for domain-specific patterns
   - ISO guidance retrieval
4. **Control Generation**: LLM generates tailored controls using retrieved context
5. **User Selection**: Present controls in popup for selection
6. **Data Storage**: Save selected controls to MongoDB + Neo4j + vector DB

### Query Handling Flow

1. **Complex Queries**: "Show financial risks using A.8 controls"
2. **Graph Traversal**: Neo4j cypher queries for relationships
3. **Response Synthesis**: LLM formats comprehensive answer

## API Endpoints

### Core Agent

- `POST /controls/chat` - Main chat interface
- `POST /controls/select-controls` - Handle control selections
- `GET /controls/user-controls` - Get all user controls

### RAG Search

- `POST /search/similar-risks` - Vector search for similar risks
- `POST /search/similar-controls` - Vector search for controls
- `POST /search/comprehensive` - Multi-source context retrieval

### Knowledge Graph

- `POST /kg/initialize-user` - Setup user in knowledge graph
- `GET /kg/user-stats` - Get user risk/control statistics
- `GET /kg/similar-controls/{domain}/{category}` - Domain-specific recommendations

## Setup Instructions

1. **Database Setup**:

   ```bash
   # Install PostgreSQL with pgvector
   # Install Neo4j
   # MongoDB should already be running
   ```

2. **Environment Variables**:

   ```env
   MONGODB_URI=your_mongodb_uri
   NEO4J_URI=bolt://localhost:7687
   NEO4J_PASSWORD=your_password
   POSTGRES_URI=postgresql://user:pass@localhost/dbname
   OPENAI_API_KEY=your_openai_key
   ```

3. **Installation**:

   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

4. **Initialize System**:

   ```bash
   # Initialize ISO annexes in Neo4j
   curl -X POST http://localhost:8000/kg/initialize-iso-annexes

   # Initialize user in knowledge graph (after login)
   curl -X POST http://localhost:8000/kg/initialize-user \
     -H "Authorization: Bearer <token>" \
     -d '{"sync_existing_data": true}'
   ```

## Usage Examples

### Generate Controls for Specific Risk

```python
# User query: "Generate controls for risk ID-123"
# Agent will:
# 1. Classify intent as "generate_controls_specific"
# 2. Retrieve context for risk ID-123
# 3. Generate 3-5 tailored controls
# 4. Present for user selection
# 5. Store selected controls in all databases
```

### Complex Query Handling

```python
# User query: "Show me all financial risks that use A.8 controls"
# Agent will:
# 1. Classify as complex query
# 2. Execute Neo4j graph traversal
# 3. Return formatted results
```

### Interactive Control Selection

```python
# After control generation:
# 1. Agent returns pending_selection=True with session_id
# 2. Frontend shows control selection popup
# 3. User selects desired controls
# 4. POST to /controls/select-controls with session_id
# 5. Agent resumes workflow and stores selections
```

## Key Features

- **Context-Aware Generation**: Uses organization domain, existing risks, and similar patterns
- **Interactive Selection**: Handles control approval workflow seamlessly
- **Multi-Source RAG**: Combines vector search, graph traversal, and LLM generation
- **Relationship Intelligence**: Leverages knowledge graph for smart recommendations
- **Scalable Architecture**: Optimized for token usage and performance
