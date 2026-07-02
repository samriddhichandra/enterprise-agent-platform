# Enterprise Agent Platform

A production-minded reference implementation of a multi-agent AI backend for enterprise workflows.

The platform exposes a FastAPI service where a Planner Agent routes each user question to the right capability:

- Research Agent: retrieves policy and support documentation with RAG.
- Tool Agent: runs safe calculations or approved read-only SQL queries.
- Direct Agent: answers simple general questions without unnecessary tool use.

Conversation history is stored in PostgreSQL, document chunks are indexed in ChromaDB, and the application can run locally or with Docker Compose.

## Features

- FastAPI REST API with OpenAPI docs at `/docs`
- LangGraph-powered agent routing
- Retrieval-augmented generation over local enterprise documents
- Persistent vector storage with ChromaDB
- PostgreSQL-backed conversation history
- Safe AST-based calculator with no `eval`
- Read-only SQL tool with allowlisted tables and query validation
- Docker and Docker Compose support
- Pytest suite for API contracts, routing, RAG chunking, and tool guardrails

## Architecture

```text
User question
    |
    v
FastAPI /chat
    |
    v
Planner Agent
    |
    +--> Research Agent --> ChromaDB retrieval --> grounded answer
    |
    +--> Tool Agent -----> calculator or read-only SQL --> tool answer
    |
    +--> Direct Agent ---> direct answer
    |
    v
Response persisted to PostgreSQL
```

## Tech Stack

- Python 3.11
- FastAPI and Uvicorn
- LangGraph, LangChain, and OpenAI models
- ChromaDB for vector search
- PostgreSQL with SQLAlchemy async sessions
- Docker and Docker Compose
- Pytest and pytest-asyncio

## Project Structure

```text
enterprise-agent-platform/
  backend/
    main.py                 FastAPI app and route handlers
    config.py               Environment-based application settings
    agents/graph.py         Planner, Research, Tool, and Direct agent graph
    api/schemas.py          Pydantic request and response models
    database/
      models.py             SQLAlchemy models
      session.py            Async database engine/session setup
      seed.py               Demo data seeding script
    rag/pipeline.py         Document loading, chunking, embeddings, retrieval
    tools/
      calculator.py         Safe arithmetic evaluator
      sql_tool.py           Validated read-only SQL tool
  data/sample_docs/         Example documents for RAG ingestion
  docker/
    Dockerfile
    docker-compose.yml
  tests/                    Unit and API tests
  requirements.txt
  pytest.ini
  .env.example
```

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ for local development, or Docker for containerized setup
- OpenAI API key

## Environment Variables

Copy `.env.example` to `.env` and update the values for your environment.

```bash
cp .env.example .env
```

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API key used by the agents and embeddings | Required |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://agent_user:agent_pass@localhost:5432/agent_platform` |
| `CHROMA_PERSIST_DIR` | Local ChromaDB persistence directory | `./data/chroma_store` |
| `DOCS_DIR` | Directory ingested by the Research Agent | `./data/sample_docs` |
| `MODEL_NAME` | Chat model used by the agents | `gpt-4o-mini` |
| `TEMPERATURE` | Model temperature | `0.0` |
| `TOP_K` | Number of retrieved chunks used for RAG answers | `4` |
| `EMBEDDING_MODEL` | Embedding model used for document indexing | `text-embedding-3-small` |

Never commit `.env` or any file containing real secrets.

## Local Development

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Start PostgreSQL and make sure `DATABASE_URL` points to the database.

Run the API:

```bash
uvicorn backend.main:app --reload
```

Seed demo database rows for the SQL tool:

```bash
python -m backend.database.seed
```

Index the sample documents for RAG:

```bash
curl -X POST http://localhost:8000/ingest
```

Check the service:

```bash
curl http://localhost:8000/health
```

## Docker

From the project directory, start the application and PostgreSQL:

```bash
docker compose -f docker/docker-compose.yml up --build
```

The API will be available at:

```text
http://localhost:8000
```

After the containers are running, seed the database and ingest documents:

```bash
docker compose -f docker/docker-compose.yml exec app python -m backend.database.seed
curl -X POST http://localhost:8000/ingest
```

Stop the stack:

```bash
docker compose -f docker/docker-compose.yml down
```

To remove the PostgreSQL volume as well:

```bash
docker compose -f docker/docker-compose.yml down -v
```

## API Usage

Ask a document-grounded policy question:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"How many days of annual leave do employees get?\"}"
```

Ask for a calculation:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is 340 * 12?\"}"
```

Ask for an approved database lookup:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"How many employees are in the Engineering department?\"}"
```

View recent conversations:

```bash
curl http://localhost:8000/history
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Service liveness check |
| `POST` | `/chat` | Route a user question through the agent graph |
| `POST` | `/ingest` | Ingest files from `DOCS_DIR` into ChromaDB |
| `GET` | `/history` | Return the latest persisted conversations |

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

The tests are designed to cover deterministic behavior without requiring live OpenAI or PostgreSQL services where mocks or dependency overrides are appropriate.

## Security Notes

- `.env` files are ignored and must never be committed.
- The calculator parses arithmetic expressions with Python AST and does not execute arbitrary Python.
- The SQL tool only allows read-only queries against approved demo tables.
- RAG answers should be treated as grounded only in the ingested documents and reviewed before production use.
- For real deployments, use managed secret storage, rotate credentials, enable authentication, and put the API behind TLS.

## Production Checklist

- Replace demo credentials with managed secrets.
- Add authentication and authorization for API access.
- Configure structured logging and request tracing.
- Add rate limiting and request size limits.
- Run database migrations instead of relying on automatic table creation.
- Add CI for tests, linting, dependency scanning, and image scanning.
- Configure backups for PostgreSQL and vector-store data.
- Pin deployment images by digest for regulated environments.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
