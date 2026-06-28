# AIDER Execution Guide for SLM Builder

## Quick Start

```bash
# 1. Navigate to project
cd "c:\Users\Prasun Bhattacharyya\Documents\Personal Projects\SLM Builder"

# 2. Read this guide
cat docs/AIDER_EXECUTION_GUIDE.md

# 3. Start with Session 1 (Critical Fix)
aider --read backend/src/services/rag_orchestrator.py backend/src/schemas/schemas.py
```

---

## Session Execution Order

| Session | Priority | Time | Files | Status |
|---------|----------|------|-------|--------|
| 1 | 🔴 Critical | 30 min | `rag_orchestrator.py`, `schemas.py` | ⬜ Ready |
| 2 | 🔴 Critical | 15 min | `rag.py`, `vector_stores.py` | ⬜ Ready |
| 3 | 🟡 Important | 45 min | `vector_stores.py` (Chroma) | ⬜ Ready |
| 4 | 🟡 Important | 45 min | `vector_stores.py` (MongoDB) | ⬜ Ready |
| 5 | 🟡 Important | 60 min | `rag.py`, `chunking.py`, `ollama.py`, `database.py`, `schemas.py` | ⬜ Ready |
| 6 | 🟢 Epic 1 | 90 min | `database.py`, `schemas.py`, `models.py` | ⬜ Ready |
| 7 | 🔵 Frontend | 60 min | `app.routes.ts`, `app.component.*`, `app.config.ts` | ⬜ Ready |

---

## Before Each Session

```bash
# 1. Ensure backend dependencies
cd backend && uv sync

# 2. Run existing tests to establish baseline
uv run pytest tests/ -v

# 3. Start fresh AIDER instance (close previous)
```

---

## Session 1 Prompt (Copy-Paste Ready)

```
Fix the query_pipeline method in backend/src/services/rag_orchestrator.py:

1. Line 15: Replace `user_vector = self.vector_store.upsert(message)` with 
   `user_vector = await self.ollama_service.get_embedding(message)`

2. The method calls `self.vector_store.query(user_vector, top_k)` - this returns List[Chunk]
   Map these to SourceChunk objects:
   ```python
   sources = [
       SourceChunk(
           document_id=str(chunk.index),
           title="Source",
           text=chunk.text,
           score=0.0
       )
       for chunk in retrieved_chunks
   ]
   ```

3. Return `ChatResponse(answer=answer, sources=sources)`

4. Add imports at top:
   ```python
   from src.schemas.schemas import ChatResponse, SourceChunk
   ```

The method should be async and use await for both embedding and generation calls.
```

**Verify**: `cd backend && uv run pytest tests/test_api.py::test_rag_indexing_with_fake_store -v`

---

## Session 2 Prompt (Copy-Paste Ready)

```
Fix the VectorStoreFactory.get_store() call in backend/src/routers/rag.py:

Current code (line ~25):
```python
vector_store = VectorStoreFactory.get_store(pipeline.vector_store_config)
```

The factory method signature is:
```python
@staticmethod
def get_store(vector_store_type: str, vector_store_config: dict) -> IVectorStore:
```

Fix to pass both arguments:
```python
vector_store = VectorStoreFactory.get_store(
    pipeline.vector_store_type,
    pipeline.vector_store_config,
)
```

Also ensure the import is correct:
```python
from src.services.vector_stores import IVectorStore, VectorStoreFactory
```
```

**Verify**: `cd backend && uv run pytest tests/test_api.py::test_pipeline_validates_mongodb_config -v`

---

## Session 3 Prompt (Copy-Paste Ready)

```
Implement the ChromaAdapter.query method in backend/src/services/vector_stores.py.

Current placeholder returns fake data. Replace with real ChromaDB query:

1. Add chromadb import at top:
   ```python
   import chromadb
   from chromadb.config import Settings
   ```

2. In __init__, initialize the client:
   ```python
   def __init__(self, vector_store_config: dict):
       self.vector_store_config = vector_store_config
       persist_dir = vector_store_config.get("persist_dir", "./data/chroma")
       self.client = chromadb.PersistentClient(path=persist_dir)
       self.collection = self.client.get_or_create_collection("documents")
   ```

3. Implement query method:
   ```python
   def query(self, vector: List[float], top_k: int) -> List[Chunk]:
       results = self.collection.query(
           query_embeddings=[vector],
           n_results=top_k,
           include=["documents", "metadatas", "distances"]
       )
       chunks = []
       if results["documents"] and results["documents"][0]:
           for i, (doc, metadata, distance) in enumerate(zip(
               results["documents"][0],
               results["metadatas"][0] if results["metadatas"] else [{}] * len(results["documents"][0]),
               results["distances"][0] if results["distances"] else [0.0] * len(results["documents"][0])
           )):
               chunks.append(Chunk(
                   text=doc,
                   index=metadata.get("index", i) if metadata else i
               ))
       return chunks
   ```

4. Also implement upsert method (required by IVectorStore):
   ```python
   def upsert(self, chunks: List[Chunk]) -> None:
       # This will be called with pre-embedded chunks from the index endpoint
       # For now, store text and generate embeddings via Ollama in the index endpoint
       pass  # Implementation in index endpoint
   ```

Note: The actual embedding generation happens in the index endpoint, not here.
```

**Verify**: `cd backend && uv run python -c "from src.services.vector_stores import ChromaAdapter; adapter = ChromaAdapter({'persist_dir': './data/chroma'}); print('ChromaAdapter initialized successfully')"`

---

## Session 4 Prompt (Copy-Paste Ready)

```
Implement the MongoDBAdapter.query method in backend/src/services/vector_stores.py.

Current implementation uses .find() - replace with proper $vectorSearch aggregation:

1. Update __init__ to accept index_name from config:
   ```python
   def __init__(self, uri: str, database_name: str, collection_name: str, index_name: str = "default"):
       self.client = MongoClient(uri)
       self.db = self.client[database_name]
       self.collection = self.db[collection_name]
       self.index_name = index_name
   ```

2. Update VectorStoreFactory.get_store to pass index_name:
   ```python
   elif vector_store_type == "mongodb":
       return MongoDBAdapter(
           vector_store_config["uri"],
           vector_store_config["database"],
           vector_store_config["collection"],
           vector_store_config.get("index_name", "default")
       )
   ```

3. Implement query with $vectorSearch:
   ```python
   def query(self, vector: List[float], top_k: int) -> List[Chunk]:
       try:
           pipeline = [
               {
                   "\$vectorSearch": {
                       "index": self.index_name,
                       "queryVector": vector,
                       "limit": top_k,
                       "path": "embedding"
                   }
               },
               {
                   "\$project": {
                       "text": 1,
                       "index": 1,
                       "_id": 0,
                       "score": {"\$meta": "vectorSearchScore"}
                   }
               }
           ]
           results = list(self.collection.aggregate(pipeline))
           chunks = []
           for i, result in enumerate(results):
               chunks.append(Chunk(
                   text=result.get("text", ""),
                   index=result.get("index", i)
               ))
           return chunks
       except PyMongoError as e:
           raise ValueError(f"MongoDB query failed: {e}") from e
   ```

Note: Requires MongoDB Atlas with a vector search index named "default" (or configured name).
```

**Verify**: `cd backend && uv run python -c "from src.services.vector_stores import MongoDBAdapter; print('MongoDBAdapter syntax OK')"`

---

## Session 5 Prompt (Copy-Paste Ready)

```
Implement the document ingestion endpoints in backend/src/routers/rag.py.

Add these three endpoints to the existing router:

1. POST /pipelines/{pipeline_id}/documents - Add text document
2. POST /pipelines/{pipeline_id}/upload - Upload file (.txt, .md)
3. POST /pipelines/{pipeline_id}/index - Index all documents

Implementation:

```python
# Add imports at top
from src.services.chunking import chunk_text
from src.services.ollama import OllamaService
from src.services.vector_stores import VectorStoreFactory, Chunk
from src.database import Model
from fastapi import UploadFile, File
import uuid

# Need to add Document model to database.py first:
class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipeline.id"), index=True)
    title = Column(String)
    content = Column(String)
    chunk_count = Column(Integer, default=0)

# And DocumentCreate/DocumentRecord schemas to schemas.py:
class DocumentCreate(BaseModel):
    title: str
    content: str

class DocumentRecord(BaseModel):
    id: int
    title: str
    chunk_count: int
    class Config:
        from_attributes = True

# 1. Add document (text content)
@router.post("/pipelines/{pipeline_id}/documents", response_model=schemas.DocumentRecord)
async def add_document(
    pipeline_id: int,
    document: schemas.DocumentCreate,
    db: Session = Depends(get_db)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")
    
    db_doc = db_models.Document(
        pipeline_id=pipeline_id,
        title=document.title,
        content=document.content
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    chunks = chunk_text(document.content)
    db_doc.chunk_count = len(chunks)
    db.commit()
    
    return schemas.DocumentRecord.model_validate(db_doc)

# 2. Upload file
@router.post("/pipelines/{pipeline_id}/upload", response_model=schemas.DocumentRecord)
async def upload_document(
    pipeline_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(('.txt', '.md')):
        raise HTTPException(400, "Only .txt and .md files supported")
    
    content = (await file.read()).decode("utf-8")
    document = schemas.DocumentCreate(title=file.filename, content=content)
    return await add_document(pipeline_id, document, db)

# 3. Index pipeline - THE KEY ENDPOINT
@router.post("/pipelines/{pipeline_id}/index")
async def index_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(404, "Pipeline not found")
    
    # Get embedding model
    emb_model = db.query(Model).filter(Model.id == pipeline.embedding_model_id).first()
    if not emb_model:
        raise HTTPException(404, "Embedding model not found")
    
    # Get generation model for OllamaService
    gen_model = db.query(Model).filter(Model.id == pipeline.generation_model_id).first()
    
    # Initialize services
    ollama_service = OllamaService(gen_model.config)
    vector_store = VectorStoreFactory.get_store(
        pipeline.vector_store_type,
        pipeline.vector_store_config
    )
    
    # Get documents from database
    documents = db.query(db_models.Document).filter(db_models.Document.pipeline_id == pipeline_id).all()
    
    total_chunks = 0
    for doc in documents:
        chunks = chunk_text(doc.content)
        # Generate embeddings for all chunks
        embeddings = []
        for chunk in chunks:
            emb = await ollama_service.get_embedding(chunk.text)
            embeddings.append(emb)
        
        # Upsert to vector store (need to update ChromaAdapter.upsert to accept embeddings)
        # For now, store in vector store with embeddings
        # vector_store.upsert(chunks, embeddings)  # Need to modify IVectorStore interface
        
        total_chunks += len(chunks)
    
    return {"status": "indexed", "chunk_count": total_chunks}
```

NOTE: The IVectorStore.upsert interface needs to accept embeddings. Update vector_stores.py:
```python
@abstractmethod
def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None: ...
```
```

**Verify**: `cd backend && uv run pytest tests/test_api.py::test_rag_indexing_with_fake_store -v`

---

## Session 6 Prompt (Copy-Paste Ready)

```
Implement the Provider-based model management system.

1. Update database.py - Add Provider model and update Model:
```python
class Provider(Base):
    __tablename__ = "provider"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)  # "ollama", "openai", "anthropic"
    config_schema = Column(JSON)  # JSON schema for validation

class Model(Base):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("provider.id"), index=True)
    model_id = Column(String, index=True)
    display_name = Column(String, index=True)
    config = Column(JSON)  # Provider-specific config (validated against provider.config_schema)
    description = Column(String, nullable=True)
```

2. Update schemas.py - Add Provider schemas (already has CONFIG_REGISTRY):
```python
class ProviderBase(BaseModel):
    name: str
    type: str
    config_schema: Optional[Dict[str, Any]] = None

class ProviderCreate(ProviderBase):
    pass

class Provider(ProviderBase):
    id: int
    class Config:
        from_attributes = True

class ProviderInfo(BaseModel):
    name: str
    description: str
    config: ProviderConfig  # required_keys: List[str]
```

3. Update models.py router:
```python
# Add GET /providers endpoint
@router.get("/providers", response_model=List[schemas.ProviderInfo])
def list_providers():
    return [
        schemas.ProviderInfo(
            name="Ollama",
            description="Local LLM runner",
            config=schemas.ProviderConfig(required_keys=["base_url", "model_id"])
        ),
        schemas.ProviderInfo(
            name="OpenAI",
            description="OpenAI API",
            config=schemas.ProviderConfig(required_keys=["api_key", "model_id"])
        ),
        schemas.ProviderInfo(
            name="Anthropic",
            description="Anthropic API",
            config=schemas.ProviderConfig(required_keys=["api_key", "model_id"])
        ),
    ]

# Update create_model to validate config against provider
@router.post("/", response_model=schemas.Model, status_code=201)
def create_model(model: schemas.ModelCreate, db: Session = Depends(get_db)):
    # Validate provider exists
    provider = db.query(db_models.Provider).filter(db_models.Provider.id == model.provider_id).first()
    if not provider:
        raise HTTPException(400, "Provider not found")
    
    # Validate config against provider's config_schema
    config_class = CONFIG_REGISTRY.get(provider.type)
    if config_class:
        try:
            config_class(**model.config)
        except ValidationError as e:
            raise HTTPException(422, f"Invalid config for {provider.type}: {e}")
    
    db_model = db_models.Model(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model
```

4. Seed default providers on startup (in main.py or database.py):
```python
def seed_providers(db: Session):
    defaults = [
        {"name": "Ollama", "type": "ollama", "config_schema": {"base_url": "string", "model_id": "string"}},
        {"name": "OpenAI", "type": "openai", "config_schema": {"api_key": "string", "model_id": "string"}},
        {"name": "Anthropic", "type": "anthropic", "config_schema": {"api_key": "string", "model_id": "string"}},
    ]
    for p in defaults:
        if not db.query(Provider).filter(Provider.type == p["type"]).first():
            db.add(Provider(**p))
    db.commit()
```
```

**Verify**: `cd backend && uv run pytest tests/test_api.py::test_model_crud -v`

---

## Session 7 Prompt (Copy-Paste Ready)

```
Set up Angular routing for the SLM Builder frontend.

1. Update app.routes.ts:
```typescript
import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/models', pathMatch: 'full' },
  { path: 'models', loadComponent: () => import('./components/model-list/model-list.component').then(m => m.ModelListComponent) },
  { path: 'pipelines', loadComponent: () => import('./components/pipeline-list/pipeline-list.component').then(m => m.PipelineListComponent) },
  { path: 'playground', loadComponent: () => import('./components/chat-playground/chat-playground.component').then(m => m.ChatPlaygroundComponent) },
  { path: '**', redirectTo: '/models' }
];
```

2. Update app.component.html to use router-outlet with sidebar:
```html
<div class="app-layout">
  <aside class="sidebar">
    <nav>
      <a routerLink="/models" routerLinkActive="active">Models</a>
      <a routerLink="/pipelines" routerLinkActive="active">Pipelines</a>
      <a routerLink="/playground" routerLinkActive="active">Playground</a>
    </nav>
  </aside>
  <main class="content">
    <router-outlet></router-outlet>
  </main>
</div>
```

3. Update app.component.css for layout:
```css
.app-layout { display: flex; height: 100vh; }
.sidebar { width: 240px; background: #f5f5f5; padding: 1rem; border-right: 1px solid #ddd; }
.sidebar nav { display: flex; flex-direction: column; gap: 0.5rem; }
.sidebar a { padding: 0.5rem 1rem; border-radius: 4px; text-decoration: none; color: #333; }
.sidebar a.active { background: #007bff; color: white; }
.content { flex: 1; padding: 2rem; overflow: auto; }
```

4. Update app.config.ts to provide router:
```typescript
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [provideRouter(routes)]
};
```
```

**Verify**: `cd frontend && npm start` → Navigate to http://localhost:4200

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/AIDER_DETAILED_PLAN.md` | Full implementation plan with all phases |
| `docs/AIDER_QUICK_REFERENCE.md` | Cheat sheet for commands, schemas, patterns |
| `docs/AIDER_SESSION_PLAN.md` | This file - session-by-session breakdown |
| `docs/SPRINT_PLANS.md` | Original sprint plans from project |
| `docs/AIDER_CONTEXT.md` | Current architecture state |
| `docs/ARCHITECTURE.md` | System architecture documentation |
| `docs/CURRENT_TASK.md` | Current task: Rich Model Management |
| `docs/BACKLOG.md` | Full implementation backlog |

---

## Troubleshooting

### Import Errors
```bash
# Check Python path
cd backend && uv run python -c "import src; print('OK')"

# Reinstall
uv sync --reinstall
```

### Test Failures
```bash
# Run with more output
uv run pytest tests/ -v --tb=long

# Run single test
uv run pytest tests/test_api.py::test_health -v
```

### Database Issues
```bash
# Reset database
rm backend/data/db.sqlite
cd backend && uv run python -c "from src.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### Ollama Connection
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

---

## Success Criteria (All Sessions Complete)

- [ ] `GET /health` → 200 OK
- [ ] `POST /api/models` → Creates model with provider config
- [ ] `POST /api/pipelines` → Creates pipeline with vector store
- [ ] `POST /api/rag/pipelines/{id}/documents` → Adds document
- [ ] `POST /api/rag/pipelines/{id}/upload` → Uploads file
- [ ] `POST /api/rag/pipelines/{id}/index` → Indexes documents
- [ ] `POST /api/rag/pipelines/{id}/chat` → Returns ChatResponse with sources
- [ ] Frontend: Navigation between Models/Pipelines/Playground works
- [ ] All tests pass: `uv run pytest tests/ -v`

---

## Next Steps After Completion

1. **Add authentication** - JWT tokens for API security
2. **Implement background jobs** - Async indexing with status polling
3. **Add more vector stores** - Pinecone, Weaviate, Qdrant
4. **Improve frontend** - Separate components, better UX
5. **Add evaluation** - RAGAS metrics for pipeline quality
6. **Deploy** - Docker, Kubernetes, CI/CD