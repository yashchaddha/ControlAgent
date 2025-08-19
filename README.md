# ISO27001 Control Generation Agent Backend

An AI-powered backend system for generating ISO 27001 Annex A controls using Retrieval-Augmented Generation (RAG) and Knowledge Graph technology.

## Features

- **AI-Powered Control Generation**: Uses OpenAI LLMs to generate ISO 27001 controls from risk descriptions
- **RAG Pipeline**: Combines vector search with knowledge graph augmentation for context-aware generation
- **Multi-Database Architecture**: MongoDB (source of truth), Postgres + pgvector (embeddings), Neo4j (knowledge graph)
- **JWT Authentication**: Secure user management with role-based access control
- **Provenance Tracking**: Full audit trail of AI-generated content
- **Vector Search**: Semantic search capabilities using OpenAI embeddings
- **Knowledge Graph**: Graph-based relationships between risks, controls, assets, and compliance frameworks

## Architecture

```
+---------+        +----------------+        +-----------+         +----------+
| Frontend| <----> | FastAPI        | <----> | Workers   | <---->  | OpenAI   |
| (React) |        | Orchestrator   |        | (Celery)  |         | LLM/Emb  |
+---------+        +----------------+        +-----------+         +----------+
                        |   |   |
                        |   |   +--> Postgres (pgvector)  [vector store]
                        |   +------> Neo4j (knowledge graph)
                        +---------> MongoDB (source-of-truth)
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd control
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your_secure_jwt_secret_here
```

### 3. Start Services

```bash
docker-compose up -d
```

This will start:

- MongoDB on port 27017
- Postgres with pgvector on port 5432
- Neo4j on ports 7474 (HTTP) and 7687 (Bolt)
- Redis on port 6379
- FastAPI app on port 8000

### 4. Initialize Databases

The databases will be automatically initialized with the provided SQL and Cypher scripts.

### 5. Access the API

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Neo4j Browser: http://localhost:7474

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Create user account
- `POST /api/v1/auth/login` - Authenticate and get token

### Risks

- `POST /api/v1/risks` - Create a new risk
- `GET /api/v1/risks` - List risks with filtering
- `GET /api/v1/risks/{risk_id}` - Get specific risk
- `PATCH /api/v1/risks/{risk_id}` - Update risk
- `POST /api/v1/risks/finalize` - Finalize risk collection

### Controls

- `POST /api/v1/controls/generate` - Generate candidate controls using RAG
- `POST /api/v1/controls/finalize` - Finalize selected controls
- `GET /api/v1/controls` - List controls with filtering
- `GET /api/v1/controls/{control_id}` - Get specific control
- `DELETE /api/v1/controls/{control_id}` - Delete control

### Search

- `POST /api/v1/search/semantic` - Semantic search using embeddings
- `GET /api/v1/search/lexical` - Lexical search (placeholder)
- `GET /api/v1/search/hybrid` - Hybrid search combining both approaches

### Knowledge Graph

- `GET /api/v1/kg/risk/{risk_id}/related-controls` - Get controls related to risk
- `GET /api/v1/kg/risk/{risk_id}/context` - Get comprehensive risk context
- `GET /api/v1/kg/risk/{risk_id}/similar` - Find similar risks

## Usage Examples

### 1. Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "security_analyst",
    "email": "analyst@company.com",
    "password": "secure_password",
    "organization_name": "Acme Corp",
    "location": "New York",
    "domain": "Financial Services"
  }'
```

### 2. Create a Risk

```bash
curl -X POST "http://localhost:8000/api/v1/risks" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Contractor Access to Production Systems",
    "description": "Risk of unauthorized access to production systems by contractors",
    "category": "Access Control",
    "likelihood": "Medium",
    "impact": "High",
    "treatment_strategy": "Mitigate",
    "asset_value": "Critical",
    "department": "IT Security"
  }'
```

### 3. Generate Controls

```bash
curl -X POST "http://localhost:8000/api/v1/controls/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_id_here",
    "risk_id": "risk_id_here",
    "annex_filter": "A.9",
    "num_candidates": 5
  }'
```

## Development

### Local Development Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Set up databases locally or use Docker:

```bash
# Start only the databases
docker-compose up -d mongodb postgres neo4j redis
```

3. Run the application:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── models.py            # Pydantic models
├── auth.py              # Authentication logic
├── database.py          # MongoDB connection
├── postgres.py          # Postgres + pgvector operations
├── neo4j_db.py          # Neo4j operations
├── openai_service.py    # OpenAI integration
├── rag_service.py       # RAG pipeline orchestration
└── routers/             # API route handlers
    ├── __init__.py
    ├── auth.py          # Authentication endpoints
    ├── risks.py         # Risk management
    ├── controls.py      # Control generation
    ├── search.py        # Search functionality
    └── kg.py            # Knowledge graph queries
```

## Configuration

### Environment Variables

| Variable         | Description                | Default                                                      |
| ---------------- | -------------------------- | ------------------------------------------------------------ |
| `MONGODB_URI`    | MongoDB connection string  | `mongodb://localhost:27017/isoriskagent`                     |
| `POSTGRES_DSN`   | Postgres connection string | `postgresql://postgres:postgres@localhost:5432/isoriskagent` |
| `NEO4J_URI`      | Neo4j connection string    | `bolt://localhost:7687`                                      |
| `REDIS_URL`      | Redis connection string    | `redis://localhost:6379/0`                                   |
| `OPENAI_API_KEY` | OpenAI API key             | Required                                                     |
| `JWT_SECRET_KEY` | JWT signing secret         | Required                                                     |

### Database Configuration

- **MongoDB**: Document store for users, risks, controls, and provenance
- **Postgres + pgvector**: Vector embeddings for semantic search
- **Neo4j**: Knowledge graph for relationships and graph queries
- **Redis**: Background task queue for Celery workers

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Deployment

### Production Considerations

1. **Security**:

   - Use strong JWT secrets
   - Configure CORS properly
   - Enable HTTPS
   - Use environment-specific configurations

2. **Scaling**:

   - Use connection pooling for databases
   - Implement rate limiting
   - Add monitoring and logging
   - Use production-grade Redis for Celery

3. **Monitoring**:
   - Health checks
   - Metrics collection
   - Error tracking
   - Performance monitoring

### Docker Production

```bash
# Build production image
docker build -t isoriskagent:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e ENV=production \
  -e LOG_LEVEL=info \
  --env-file .env \
  isoriskagent:latest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs`
