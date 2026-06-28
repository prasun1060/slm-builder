# AIDER CONTEXT: Backend State
Last Updated: 2026-06-28

## Current Architecture
- **Framework**: FastAPI
- **Database**: SQLAlchemy (SQLite)
- **Vector Stores**: ChromaDB, MongoDB Atlas (Adapter Pattern)
- **LLM Provider**: Ollama (Async via `httpx`)

## Folder Structure
```text
backend/
├── src/
│   ├── database.py           # SQLAlchemy models (Provider, Model, Pipeline)
│   ├── routers/              # API Endpoints (models.py, pipelines.py, rag.py)
│   ├── schemas/              # Pydantic models (schemas.py)
│   └── services/             # Business Logic (chunking.py, ollama.py, rag_orchestrator.py, vector_stores.py)
└── data/                     # Persistence (chroma/)
```

## Key Symbol Mappings
- **DB Models**: Located in `backend/src/database.py`. Aliased as `db_models` in routers.
- **Pydantic Schemas**: Located in `backend/src/schemas/schemas.py`.
- **Services**:
    - `OllamaService`: Async client for embeddings and generation.
    - `IVectorStore`: Interface for vector operations.
    - `VectorStoreFactory`: Instantiates `ChromaAdapter` or `MongoDBAdapter`.
    - `RAGOrchestrator`: Coordinates the RAG workflow.

## Dependency Flow
`routers/rag.py` $\rightarrow$ `services/rag_orchestrator.py` $\rightarrow$ (`services/vector_stores.py` & `services/ollama.py`)

## Frontend Contract (Integration Points)
- **Framework**: Angular (Standalone Components)
- **Key Files**: `frontend/src/app/app.component.ts`, `app.component.html`, `app.component.css`
- **API Endpoints Consumed**:
    - `GET/POST /models` → `Model` schema
    - `GET/POST /pipelines` → `Pipeline` schema
    - `POST /pipelines/{id}/chat` → `ChatRequest` / `ChatResponse` schema
- **Shared Schemas**: Frontend expects `ChatResponse.sources` to be `SourceChunk[]` (document_id, title, text, score).

## Current Sprint Status
- **Sprint 0 (Import Cleanup)**: COMPLETED
- **Sprint 1 (RAG Orchestration & Response Fixes)**: NEXT
- **Sprint 2 (Vector Store & Factory Correction)**: PENDING
- **Sprint 3 (Async I/O & Model Config Fixes)**: PENDING
- **Sprint 4 (Pipeline Validation & API Cleanup)**: PENDING

