# AIDER Detailed Implementation Plan

## Context Constraints
- **AIDER Context Window**: 8k tokens (~6k words)
- **Model**: Local running model (slower, less capable than cloud models)
- **Strategy**: Break work into small, self-contained tasks with minimal file context

---

## Project Overview
SLM Builder is a local-first RAG builder with:
- **Backend**: FastAPI + SQLAlchemy + SQLite + ChromaDB/MongoDB Atlas
- **Frontend**: Angular 19 (standalone components)
- **LLM Runtime**: Ollama (async via httpx)

---

## Current State Analysis

### Working Components
1. ✅ Basic FastAPI app structure (`main.py`)
2. ✅ Database models (`database.py`) - Provider, Model, Pipeline tables
3. ✅ Pydantic schemas (`schemas/schemas.py`) - Complete with provider configs
4. ✅ Model CRUD router (`routers/models.py`)
5. ✅ Pipeline CRUD router (`routers/pipelines.py`)
6. ✅ Basic RAG router (`routers/rag.py`) - chat endpoint exists
5. ✅ Ollama service (`services/ollama.py`) - async httpx implementation
6. ✅ Vector store interface (`services/vector_stores.py`) - ABC + Chroma/Mongo adapters
7. ✅ RAG Orchestrator (`services/rag_orchestrator.py`) - basic flow
8. ✅ Chunking utility (`services/chunking.py`)
9. ✅ Frontend component (`app.component.ts`) - single component MVP
10. ✅ Tests (`tests/test_api.py`) - basic coverage

### Known Issues (from SPRINT_PLANS.md)
1. **Sprint 1**: RAG Orchestrator - wrong method call (`upsert` instead of `get_embedding`)
2. **Sprint 2**: Vector Store Factory - missing args, Chroma/Mongo query implementations
3. **Sprint 3**: Async I/O - Ollama service needs async refactor (already done?)
4. **Sprint 4**: Pipeline validation & API cleanup

---

## Task Breakdown for AIDER

### Phase 1: Critical Bug Fixes (High Priority)

#### Task 1.1: Fix RAG Orchestrator Embedding Call
**Files**: `backend/src/services/rag_orchestrator.py`
**Context Needed**: Only this file + `schemas/schemas.py` (for ChatResponse, SourceChunk)
**Estimated Tokens**: ~500

```python
# Current buggy code in query_pipeline():
user_vector = self.vector_store.upsert(message)  # WRONG

# Should be:
user_vector = await self.ollama_service.get_embedding(message)
```

**Verification**: Run `pytest tests/test_api.py::test_rag_indexing_with_fake_store -v`

---

#### Task 1.2: Fix RAG Orchestrator Response Mapping
**Files**: `backend/src/services/rag_orchestrator.py`
**Context Needed**: Same as Task 1.1
**Estimated Tokens**: ~500

```python
# Map retrieved chunks to SourceChunk properly
sources = [
    SourceChunk(
        document_id=str(chunk.index),
        title="Source",
        text=chunk.text,
        score=0.0
    )
    for chunk in retrieved_chunks
]
return ChatResponse(answer=answer, sources=sources)
```

---

#### Task 1.3: Fix Vector Store Factory Call in rag.py
**Files**: `backend/src/routers/rag.py`
**Context Needed**: This file + `services/vector_stores.py` (for factory signature)
**Estimated Tokens**: ~600

```python
# Current (missing vector_store_type):
vector_store = VectorStoreFactory.get_store(pipeline.vector_store_config)

# Should be:
vector_store = VectorStoreFactory.get_store(
    pipeline.vector_store_type,
    pipeline.vector_store_config,
)
```

---

### Phase 2: Vector Store Implementation (Medium Priority)

#### Task 2.1: Implement ChromaAdapter.query Properly
**Files**: `backend/src/services/vector_stores.py`
**Context Needed**: This file only (self-contained)
**Estimated Tokens**: ~800

```python
# Current placeholder returns fake data
# Need to implement actual ChromaDB query using chromadb client
```

**Dependencies**: `chromadb` package (already in pyproject.toml)

---

#### Task 2.2: Implement MongoDBAdapter.query with $vectorSearch
**Files**: `backend/src/services/vector_stores.py`
**Context Needed**: This file only
**Estimated Tokens**: ~800

```python
# Current uses .find() - needs $vectorSearch aggregation
pipeline = [
    {"$vectorSearch": {
        "index": "default",  # or from config
        "queryVector": vector,
        "limit": top_k,
        "path": "embedding"
    }},
    {"$project": {"text": 1, "_id": 0}}
]
```

---

#### Task 2.3: Implement ChromaAdapter.upsert
**Files**: `backend/src/services/vector_stores.py`
**Context Needed**: This file only
**Estimated Tokens**: ~600

```python
# Currently missing upsert implementation
# Need to add documents to Chroma collection with embeddings
```

---

### Phase 3: Document Ingestion & Indexing (Medium Priority)

#### Task 3.1: Implement Document Upload Endpoint
**Files**: `backend/src/routers/rag.py`
**Context Needed**: This file + `services/chunking.py` + `services/vector_stores.py`
**Estimated Tokens**: ~1000

**Endpoints to implement**:
- `POST /api/rag/pipelines/{pipeline_id}/documents` - text content
- `POST /api/rag/pipelines/{pipeline_id}/upload` - file upload
- `POST /api/rag/pipelines/{pipeline_id}/index` - trigger indexing

---

#### Task 3.2: Connect Chunking to Vector Store
**Files**: `backend/src/routers/rag.py` (index endpoint)
**Context Needed**: This file + `services/chunking.py` + `services/vector_stores.py`
**Estimated Tokens**: ~800

```python
# In index endpoint:
chunks = chunk_text(document.content)
embeddings = await ollama_service.get_embeddings([c.text for c in chunks])
vector_store.upsert(chunks, embeddings)
```

---

### Phase 4: Model Provider System (Lower Priority - Backlog Epic 1)

#### Task 4.1: Add Provider Table & Model Migration
**Files**: `backend/src/database.py`
**Context Needed**: This file only
**Estimated Tokens**: ~500

```python
# Add Provider model, update Model with provider_id FK
```

---

#### Task 4.2: Add Provider Schemas & Validation
**Files**: `backend/src/schemas/schemas.py`
**Context Needed**: This file only (already has CONFIG_REGISTRY)
**Estimated Tokens**: ~600

---

#### Task 4.3: Update Models Router for Provider Logic
**Files**: `backend/src/routers/models.py`
**Context Needed**: This file + `schemas/schemas.py` + `database.py`
**Estimated Tokens**: ~1000

---

### Phase 5: Frontend Improvements (Separate Session)

#### Task 5.1: Add Routing & Navigation
**Files**: `frontend/src/app/app.routes.ts`, `frontend/src/app/app.component.html`
**Context Needed**: These files only
**Estimated Tokens**: ~800

---

#### Task 5.2: Split Components
**Files**: New component files in `frontend/src/app/components/`
**Context Needed**: One component at a time
**Estimated Tokens**: ~600 per component

---

## Recommended AIDER Workflow

### Session 1: Critical Fixes (Tasks 1.1 - 1.3)
```bash
# Run these in sequence, each in a fresh AIDER session
aider backend/src/services/rag_orchestrator.py
aider backend/src/routers/rag.py
```

### Session 2: Vector Store Implementation (Tasks 2.1 - 2.3)
```bash
aider backend/src/services/vector_stores.py
```

### Session 3: Document Ingestion (Tasks 3.1 - 3.2)
```bash
aider backend/src/routers/rag.py
```

### Session 4: Model Provider System (Tasks 4.1 - 4.3)
```bash
aider backend/src/database.py
aider backend/src/schemas/schemas.py
aider backend/src/routers/models.py
```

---

## Context Management Tips for AIDER

### 1. Use `--read` to limit context
```bash
aider --read backend/src/services/rag_orchestrator.py backend/src/schemas/schemas.py
```

### 2. Provide focused prompts
```
"Fix the query_pipeline method in rag_orchestrator.py:
- Line X: Change `self.vector_store.upsert(message)` to `await self.ollama_service.get_embedding(message)`
- Map returned chunks to SourceChunk objects for ChatResponse
- Import ChatResponse and SourceChunk from src.schemas.schemas"
```

### 3. Run tests after each fix
```bash
cd backend && uv run pytest tests/test_api.py -v
```

### 4. Commit after each working change
```bash
git add -A && git commit -m "fix: rag orchestrator embedding call"
```

---

## File Reference Quick Links

| Component | File Path |
|-----------|-----------|
| Main App | `backend/main.py` |
| Database Models | `backend/src/database.py` |
| Schemas | `backend/src/schemas/schemas.py` |
| Models Router | `backend/src/routers/models.py` |
| Pipelines Router | `backend/src/routers/pipelines.py` |
| RAG Router | `backend/src/routers/rag.py` |
| Ollama Service | `backend/src/services/ollama.py` |
| Vector Stores | `backend/src/services/vector_stores.py` |
| RAG Orchestrator | `backend/src/services/rag_orchestrator.py` |
| Chunking | `backend/src/services/chunking.py` |
| Frontend Main | `frontend/src/app/app.component.ts` |
| Frontend Routes | `frontend/src/app/app.routes.ts` |
| Tests | `backend/tests/test_api.py` |

---

## Environment Setup Commands

```bash
# Backend
cd backend
uv sync
uv run uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start

# Tests
cd backend
uv run pytest tests/ -v
```

---

## Success Criteria Checklist

- [ ] `GET /health` returns 200
- [ ] `POST /api/models` creates model with provider config
- [ ] `POST /api/pipelines` creates pipeline with vector store config
- [ ] `POST /api/rag/pipelines/{id}/documents` adds document
- [ ] `POST /api/rag/pipelines/{id}/index` indexes documents
- [ ] `POST /api/rag/pipelines/{id}/chat` returns ChatResponse with sources
- [ ] Frontend can create model → pipeline → add docs → chat
- [ ] All tests pass: `pytest tests/ -v`

---

## Notes for AIDER

1. **Always run tests after changes** - the test file shows expected behavior
2. **Check imports carefully** - the project uses `src.` prefix imports
3. **Async/await** - all network calls must be async (httpx, not requests)
4. **Pydantic v2** - use `model_dump()` not `dict()`, `model_validate()` not `parse_obj()`
5. **SQLAlchemy 2.0** - use `select()` not `query()` for new code
6. **Don't modify frontend** unless explicitly asked - backend-first approach