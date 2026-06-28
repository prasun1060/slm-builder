# Backend Fixes – Detailed Sprint Plans for Aider

The following plans are broken into **four independent sprints**. Each sprint is self‑contained, references explicit file paths, and includes verification steps. Aider can execute each sprint sequentially, using the updated `AIDER_CONTEXT.md` and `ARCHITECTURE.md` as its source of truth.

---

## Sprint 1 – RAG Orchestration & Response Fixes
**Goal:** Ensure the RAG pipeline returns a valid `ChatResponse` and uses embeddings correctly.

### 1.1 Update `backend/src/services/rag_orchestrator.py`
- **Replace upsert with embedding call**
  ```python
  # Old (buggy)
  user_vector = self.vector_store.upsert(message)
  # New (correct)
  user_vector = await self.ollama_service.get_embedding(message)
  ```
- **Map retrieved `Chunk` objects to `SourceChunk`** before returning:
  ```python
  sources = [
      SourceChunk(
          document_id=str(chunk.index),
          title="Source",
          text=chunk.text,
          score=0.0  # placeholder – real score not available yet
      )
      for chunk in retrieved_chunks
  ]
  return ChatResponse(answer=answer, sources=sources)
  ```
- **Add import** if missing:
  ```python
  from src.schemas.schemas import ChatResponse, SourceChunk
  ```

### 1.2 Verify
1. Run `pytest -q tests/test_api.py` (or the Aider test command) and ensure the `/pipelines/{id}/chat` endpoint returns a JSON matching the `ChatResponse` schema (no validation errors).
2. Manually call the endpoint via `curl` or the test client and inspect the `sources` array – it should be a list of objects with `document_id`, `title`, `text`, `score`.

---

## Sprint 2 – Vector Store & Factory Corrections
**Goal:** Fix import errors, correct factory usage, and implement proper vector search.

### 2.1 Fix `backend/src/routers/rag.py`
- **Correct factory call** (currently missing `vector_store_type` argument):
  ```python
  vector_store = VectorStoreFactory.get_store(
      pipeline.vector_store_type,
      pipeline.vector_store_config,
  )
  ```
- Ensure the import line for `VectorStoreFactory` remains unchanged.

### 2.2 Update `backend/src/services/vector_stores.py`
- **Define `IVectorStore`** (if not already present) as an abstract base class with `upsert` and `query` signatures.
- **ChromaAdapter.query**: Return the correct index for each document instead of hard‑coded `0`.
  ```python
  for i, doc in enumerate(results):
      chunks.append(Chunk(text=doc, index=i))
  ```
- **MongoDBAdapter.query**: Replace the placeholder `.find({...})` with a proper `$vectorSearch` aggregation pipeline. Example skeleton:
  ```python
  pipeline = [
      {"$vectorSearch": {
          "index": "default",
          "queryVector": vector,
          "limit": top_k,
          "path": "embedding"
      }},
      {"$project": {"text": 1, "_id": 0}}
  ]
  docs = self.collection.aggregate(pipeline)
  for doc in docs:
      chunks.append(Chunk(text=doc["text"], index=doc.get("_id", 0)))
  ```
- Add a comment explaining that the `$vectorSearch` stage requires a vector index named `default` (adjust if your index name differs).

### 2.3 Verify
1. Start the FastAPI server (`uvicorn backend.main:app --reload`).
2. Hit the `/pipelines/{id}/chat` endpoint with a simple message. The response should contain `sources` with at least one chunk.
3. Inspect the logs – there should be no `ImportError` or `TypeError` from the factory.

---

## Sprint 3 – Async I/O & Model Config Fixes
**Goal:** Remove blocking I/O and ensure the correct model configuration is used.

### 3.1 Refactor `backend/src/services/ollama.py`
- Replace `import requests` with `import httpx`.
- Convert the three public methods to `async def` and use `await httpx.AsyncClient().post(...)`.
- Example for `generate`:
  ```python
  async def generate(self, prompt: str) -> str:
      async with httpx.AsyncClient() as client:
          resp = await client.post(f"{self.base_url}/api/generate", json={"prompt": prompt, "model": self.model_id, "stream": False}, timeout=self.timeout)
          resp.raise_for_status()
          return resp.json()["response"]
  ```
- Apply similar changes to `get_embedding` and `health_check`.
- Update any type hints to `Awaitable[str]` if needed.

### 3.2 Update `backend/src/routers/rag.py`
- **Await the Ollama calls** now that they are async:
  ```python
  embedding = await ollama_service.get_embedding(message)
  answer = await ollama_service.generate(prompt)
  ```
- **Fetch the correct model config** instead of using a non‑existent `pipeline.config`:
  ```python
  generation_model = db.session.get(db_models.Model, pipeline.generation_model_id)
  ollama_service = OllamaService(model_config=generation_model.config)
  ```
- Ensure `db.session` is imported from `src.database` and that `db_models` alias is used consistently.

### 3.3 Verify
1. Run the server and call the chat endpoint – the request should complete without a `RuntimeError: Event loop is closed` or blocking warnings.
2. Confirm that the `OllamaService` is instantiated with the model configuration from the `Model` table (inspect the request payload in logs).

---

## Sprint 4 – Pipeline Validation & API Cleanup
**Goal:** Harden pipeline creation and clean up unused imports.

### 4.1 Fix `backend/src/routers/pipelines.py`
- **Validate both model IDs** when creating or updating a pipeline:
  ```python
  _ensure_model_exists(db, pipeline.embedding_model_id)
  _ensure_model_exists(db, pipeline.generation_model_id)
  ```
- Update any references to `pipeline.model_id` (which does not exist) to the correct fields.

### 4.2 Clean `backend/main.py`
- Remove the line that includes a non‑existent router:
  ```python
  # app.include_router(vector_stores.router)  # <-- delete this line
  ```
- Verify that only existing routers (`models`, `pipelines`, `rag`) are included.

### 4.3 Verify
1. Run the full test suite (`pytest`). All tests should pass.
2. Use the OpenAPI docs (`/docs`) to ensure the `/pipelines` endpoints accept both `embedding_model_id` and `generation_model_id` fields.
3. Start the server and confirm there are no import‑related tracebacks on startup.

---

## General Verification Checklist (run after each sprint)
- **Static analysis:** `python -m pyright .` – no type errors.
- **Linting:** `ruff check .` – no lint failures.
- **Tests:** `pytest -q` – all tests pass.
- **Manual API sanity check:** Use `curl` or the Swagger UI to hit each endpoint and verify JSON schema compliance.

---

### How Aider Should Use This Plan
1. **Read `docs/AIDER_CONTEXT.md` and `docs/ARCHITECTURE.md`** to understand the current architecture and symbol locations.
2. **Open this file (`SPRINT_PLANS.md`)** and work on the first sprint listed.
3. **After completing a sprint**, mark it as `COMPLETED` (you can edit the markdown to add a ✅) and move to the next sprint.
4. **Do not attempt to solve later‑sprint issues before the current sprint is verified**, as many fixes depend on earlier changes (e.g., async Ollama calls are required before the RAG orchestrator can use them).

Feel free to ask for clarification on any step before proceeding.
