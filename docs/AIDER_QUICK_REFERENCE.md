# AIDER Quick Reference Card

## Project: SLM Builder
**Backend**: FastAPI + SQLAlchemy + ChromaDB/MongoDB + Ollama
**Frontend**: Angular 19 (standalone)
**Package Manager**: uv (backend), npm (frontend)

---

## Key Commands

```bash
# Backend
cd backend
uv sync                    # Install deps
uv run uvicorn main:app --reload  # Dev server
uv run pytest tests/ -v    # Run tests

# Frontend
cd frontend
npm install
npm start                  # Dev server on :4200
```

---

## Critical Files (Memorize These Paths)

```
backend/
├── main.py                           # FastAPI app entry
├── src/
│   ├── database.py                   # SQLAlchemy models
│   ├── schemas/schemas.py            # Pydantic models (SOURCE OF TRUTH)
│   ├── routers/
│   │   ├── models.py                 # Model CRUD
│   │   ├── pipelines.py              # Pipeline CRUD
│   │   └── rag.py                    # RAG endpoints (chat, index, docs)
│   └── services/
│       ├── ollama.py                 # Async Ollama client
│       ├── vector_stores.py          # IVectorStore + adapters
│       ├── rag_orchestrator.py       # RAG flow coordinator
│       └── chunking.py               # Text chunking utility
└── tests/test_api.py                 # Integration tests
```

---

## Current Sprint: Fix RAG Orchestration

### Bug 1: Wrong method in rag_orchestrator.py
**File**: `backend/src/services/rag_orchestrator.py`
**Line**: ~15 in `query_pipeline()`
```python
# BUG:
user_vector = self.vector_store.upsert(message)

# FIX:
user_vector = await self.ollama_service.get_embedding(message)
```

### Bug 2: Missing imports in rag_orchestrator.py
```python
from src.schemas.schemas import ChatResponse, SourceChunk
```

### Bug 3: Factory call missing arg in rag.py
**File**: `backend/src/routers/rag.py`
**Line**: ~25
```python
# BUG:
vector_store = VectorStoreFactory.get_store(pipeline.vector_store_config)

# FIX:
vector_store = VectorStoreFactory.get_store(
    pipeline.vector_store_type,
    pipeline.vector_store_config,
)
```

---

## Schemas Reference (from schemas/schemas.py)

```python
# Core models
class ModelBase(BaseModel):
    display_name: str
    model_id: str
    provider_id: int
    config: Dict[str, Any] = {}
    description: Optional[str] = None

class PipelineBase(BaseModel):
    name: str
    embedding_model_id: int
    generation_model_id: int
    vector_store_type: str
    vector_store_config: Dict[str, Any] = {}

# Chat
class ChatRequest(BaseModel):
    message: str
    top_k: int = 3

class SourceChunk(BaseModel):
    document_id: str
    title: str
    text: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]

# Provider configs (for validation)
CONFIG_REGISTRY = {
    "ollama": OllamaConfig,      # base_url, timeout
    "openai": OpenAIConfig,      # api_key, org_id, base_url
    "anthropic": AnthropicConfig # api_key, base_url
}
```

---

## Vector Store Interface (from vector_stores.py)

```python
class IVectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: List[Chunk]) -> None: ...
    @abstractmethod
    def query(self, vector: List[float], top_k: int) -> List[Chunk]: ...
    @abstractmethod
    def delete(self, document_id: str): ...
    @abstractmethod
    def clear_collection(self): ...

class Chunk:  # from schemas
    text: str
    index: int
```

---

## Test Commands

```bash
# Run all tests
cd backend && uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_api.py::test_health -v
uv run pytest tests/test_api.py::test_model_crud -v
uv run pytest tests/test_api.py::test_pipeline_validates_mongodb_config -v
uv run pytest tests/test_api.py::test_rag_indexing_with_fake_store -v
```

---

## Common Patterns

### Async HTTP (httpx)
```python
async with httpx.AsyncClient() as client:
    resp = await client.post(url, json=data, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

### SQLAlchemy 2.0 Session
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In router:
def endpoint(db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.id == id).first()
```

### Pydantic v2
```python
# Serialization
model.model_dump()           # not .dict()
model.model_dump(exclude_unset=True)

# Validation
Model.model_validate(data)   # not .parse_obj()
```

---

## AIDER Session Template

```bash
# 1. Start with minimal context
aider --read backend/src/services/rag_orchestrator.py backend/src/schemas/schemas.py

# 2. Give focused prompt
"Fix query_pipeline method:
1. Line 15: Change self.vector_store.upsert(message) to await self.ollama_service.get_embedding(message)
2. Map retrieved chunks to SourceChunk objects
3. Return ChatResponse(answer=answer, sources=sources)
4. Add imports for ChatResponse, SourceChunk from src.schemas.schemas"

# 3. Verify
cd backend && uv run pytest tests/test_api.py::test_rag_indexing_with_fake_store -v

# 4. Commit
git add -A && git commit -m "fix: rag orchestrator embedding and response"
```

---

## Don't Touch (Unless Asked)

- `frontend/` - Separate Angular work
- `backend/src/services/vector_stores.py` - Until Phase 2
- `backend/src/database.py` - Until Phase 4 (provider migration)
- Test files - They define expected behavior

---

## Environment Variables

```bash
# Backend/.env (optional)
DATABASE_URL=sqlite:///./data/db.sqlite
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_PERSIST_DIR=./data/chroma
MONGODB_URI=mongodb://...
MONGODB_DATABASE=slm_builder
MONGODB_COLLECTION=documents
MONGODB_VECTOR_INDEX=default
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET/POST | /api/models | Model CRUD |
| GET/POST | /api/pipelines | Pipeline CRUD |
| GET | /api/pipelines/vector-stores | List vector store types |
| POST | /api/rag/pipelines/{id}/documents | Add text document |
| POST | /api/rag/pipelines/{id}/upload | Upload file |
| POST | /api/rag/pipelines/{id}/index | Index documents |
| POST | /api/rag/pipelines/{id}/chat | Chat with RAG |

---

## Next Steps After Critical Fixes

1. **Implement ChromaAdapter.query/upsert** - Real vector operations
2. **Implement MongoDBAdapter.query** - $vectorSearch pipeline
3. **Complete document ingestion** - Chunk → Embed → Store flow
4. **Add Provider table** - Multi-provider model management
5. **Frontend routing** - Split into components