# AIDER Session-Based Task Breakdown

## Overview
Each session is designed to fit within AIDER's 8k context window (~6k words).
Run each session in a **fresh AIDER instance** to avoid context pollution.

---

## SESSION 1: Fix RAG Orchestrator (Critical - 30 min)

### Files to Read
- `backend/src/services/rag_orchestrator.py` (~50 lines)
- `backend/src/schemas/schemas.py` (ChatResponse, SourceChunk only ~30 lines)

### Prompt for AIDER
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

### Verification
```bash
cd backend && uv run pytest tests/test_api.py::test_rag_indexing_with_fake_store -v
```

### Expected Result
Test passes, chat endpoint returns valid ChatResponse with sources array.

---

## SESSION 2: Fix Vector Store Factory Call (Critical - 15 min)

### Files to Read
- `backend/src/routers/rag.py` (~40 lines)
- `backend/src/services/vector_stores.py` (VectorStoreFactory signature only ~10 lines)

### Prompt for AIDER
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

### Verification
```bash
cd backend && uv run pytest tests/test_api.py::test_pipeline_validates_mongodb_config -v
```

---

## SESSION 3: Implement ChromaAdapter.query (Important - 45 min)

### Files to Read
- `backend/src/services/vector_stores.py` (full file ~80 lines)

### Prompt for AIDER
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

### Verification
```bash
cd backend && uv run python -c "
from src.services.vector_stores import ChromaAdapter
adapter = ChromaAdapter({'persist_dir': './data/chroma'})
print('ChromaAdapter initialized successfully')
"
```

---

## SESSION 4: Implement MongoDBAdapter.query (Important - 45 min)

### Files to Read
- `backend/src/services/vector_stores.py` (MongoDBAdapter class only ~30 lines)

### Prompt for AIDER
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

### Verification
```bash
cd backend && uv run python -c "
from src.services.vector_stores import MongoDBAdapter
# Test with dummy config (will fail connection but validates syntax)
try:
    adapter = MongoDBAdapter('mongodb://localhost', 'test', 'test', 'default')
    print('MongoDBAdapter initialized successfully')
except Exception as e:
    print(f'Expected connection error: {e}')
"
```

---

## SESSION 5: Complete Document Ingestion (Important - 60 min)

### Files to Read
- `backend/src/routers/rag.py` (full file ~60 lines)
- `backend/src/services/chunking.py` (~30 lines)
- `backend/src/services/vector_stores.py` (IVectorStore interface)
- `backend/src/services/ollama.py` (OllamaService.get_embedding)

### Prompt for AIDER
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
import uuid

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
    
    # Store document in database (need Document model - see note below)
    # For MVP, just chunk and return
    chunks = chunk_text(document.content)
    return schemas.DocumentRecord(
        id=len(chunks),  # placeholder
        title=document.title,
        chunk_count=len(chunks)
    )

# 2. Upload file
@router.post("/pipelines/{pipeline_id}/upload", response_model=schemas.DocumentRecord)
async def upload_document(
    pipeline_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = (await file.read()).decode("utf-8")
    # Reuse add_document logic
    ...

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
    
    # Get documents from database (need Document model)
    # For each document:
    #   chunks = chunk_text(doc.content)
    #   embeddings = await ollama_service.get_embeddings([c.text for c in chunks])
    #   vector_store.upsert(chunks, embeddings)
    
    return {"status": "indexed", "chunk_count": total_chunks}
```

NOTE: Need to add Document SQLAlchemy model to database.py first:
```python
class Document(Base):
    __tablename__ = "document"
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipeline.id"), index=True)
    title = Column(String)
    content = Column(String)
    chunk_count = Column(Integer, default=0)
```

And add DocumentCreate/DocumentRecord schemas to schemas.py.
```

### Verification
```bash
cd backend && uv run pytest tests/test_api.py::test_rag_indexing_with_fake_store -v
```

---

## SESSION 6: Add Provider System (Epic 1 - 90 min)

### Files to Read
- `backend/src/database.py` (full ~50 lines)
- `backend/src/schemas/schemas.py` (Provider/Config sections ~60 lines)
- `backend/src/routers/models.py` (full ~60 lines)

### Prompt for AIDER
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

### Verification
```bash
cd backend && uv run pytest tests/test_api.py::test_model_crud -v
cd backend && uv run python -c "
from src.database import get_db, Provider
db = next(get_db())
providers = db.query(Provider).all()
for p in providers:
    print(f'{p.name} ({p.type})')
"
```

---

## SESSION 7: Frontend Routing (Separate - 60 min)

### Files to Read
- `frontend/src/app/app.routes.ts` (empty)
- `frontend/src/app/app.component.html` (current single component)
- `frontend/src/app/app.component.ts` (current logic)

### Prompt for AIDER
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

### Verification
```bash
cd frontend && npm start
# Navigate to http://localhost:4200 - should show sidebar with navigation
```

---

## Running Order Summary

```bash
# Session 1: Critical fix
aider --read backend/src/services/rag_orchestrator.py backend/src/schemas/schemas.py

# Session 2: Critical fix  
aider --read backend/src/routers/rag.py backend/src/services/vector_stores.py

# Session 3: Vector store
aider --read backend/src/services/vector_stores.py

# Session 4: Vector store
aider --read backend/src/services/vector_stores.py

# Session 5: Document ingestion
aider --read backend/src/routers/rag.py backend/src/services/chunking.py backend/src/services/vector_stores.py backend/src/services/ollama.py backend/src/database.py backend/src/schemas/schemas.py

# Session 6: Provider system
aider --read backend/src/database.py backend/src/schemas/schemas.py backend/src/routers/models.py

# Session 7: Frontend (separate)
aider --read frontend/src/app/app.routes.ts frontend/src/app/app.component.html frontend/src/app/app.component.ts frontend/src/app/app.config.ts
```

---

## Context Management Rules

1. **One session = one task** - Don't combine sessions
2. **Use `--read`** - Only load files you need
3. **Run tests after each session** - Verify before moving on
4. **Commit after each session** - `git add -A && git commit -m "session N: description"`
5. **Fresh AIDER instance per session** - Clear context completely