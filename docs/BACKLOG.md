# SLM Builder Implementation Backlog

## Epic 1: Backend Foundation & Core Infrastructure
*Goal: Establish a stable, type-safe, and extensible backend core.*

### Task 1.1: Module Layout & Dependency Stabilization
- **Objective:** Fix broken imports and align directory structure with `pyproject.toml`.
- **Affected Files:** `backend/main.py`, `backend/src/__init__.py`, `backend/pyproject.toml`.
- **Acceptance Criteria:** `uv sync` completes; `uv run uvicorn main:app` starts without `ImportError`.

### Task 1.2: Metadata Database Schema (SQLAlchemy)
- **Objective:** Implement `providers`, `models`, `pipelines`, and `documents` tables.
- **Affected Files:** `backend/src/database.py`, `backend/src/schemas/__init__.py`.
- **Acceptance Criteria:** Database initializes on startup; tables are created in SQLite.

### Task 1.3: Provider-Based Model Management API
- **Objective:** Implement CRUD for `providers` and `models` using JSON config.
- **Affected Files:** `backend/src/routers/models.py`, `backend/src/schemas/__init__.py`.
- **Acceptance Criteria:** `POST /api/models` validates config based on provider; `GET /api/providers` returns supported runtimes.

---

## Epic 2: Vector Storage & Knowledge Ingestion
*Goal: Implement a provider-agnostic vector storage layer.*

### Task 2.1: Vector Store Interface (ABC)
- **Objective:** Define the `IVectorStore` abstract base class.
- **Affected Files:** `backend/src/services/vector_stores.py`.
- **Acceptance Criteria:** Interface defines `upsert`, `query`, `delete`, and `clear_collection`.

### Task 2.2: ChromaDB Adapter Implementation
- **Objective:** Implement `IVectorStore` using ChromaDB with local persistence.
- **Affected Files:** `backend/src/services/vector_stores.py`.
- **Acceptance Criteria:** Ability to store and retrieve embeddings in `backend/data/chroma`.

### Task 2.3: MongoDB Atlas Adapter Implementation
- **Objective:** Implement `IVectorStore` using MongoDB Atlas Vector Search.
- **Affected Files:** `backend/src/services/vector_stores.py`.
- **Acceptance Criteria:** Successful connection and query execution against MongoDB Atlas.

### Task 2.4: Document Ingestion & Chunking Service
- **Objective:** Implement `.txt`/`.md` parsing and recursive character chunking.
- **Affected Files:** `backend/src/services/chunking.py`, `backend/src/routers/rag.py`.
- **Acceptance Criteria:** Uploaded files are split into chunks and passed to the active vector store.

---

## Epic 3: RAG Orchestration & Chat
*Goal: Connect LLM runtimes to retrieved context.*

### Task 3.1: Ollama Service Integration
- **Objective:** Implement the Ollama client with health checks.
- **Affected Files:** `backend/src/services/ollama.py`.
- **Acceptance Criteria:** Ability to send a prompt and receive a response from a local Ollama instance.

### Task 3.2: RAG Query Orchestrator
- **Objective:** Implement the "Retrieve $\rightarrow$ Augment $\rightarrow$ Generate" flow.
- **Affected Files:** `backend/src/routers/rag.py`, `backend/src/services/rag_orchestrator.py`.
- **Acceptance Criteria:** `POST /api/rag/pipelines/{id}/chat` returns a grounded answer based on retrieved chunks.

### Task 3.3: Retrieval Transparency (Citations)
- **Objective:** Include source chunks in the chat response.
- **Affected Files:** `backend/src/schemas/__init__.py`, `backend/src/routers/rag.py`.
- **Acceptance Criteria:** API response includes a `sources` array with original text and metadata.

---

## Epic 4: Professional Angular Frontend
*Goal: Transform the UI into a developer-centric workspace.*

### Task 4.1: Workspace Layout & Routing
- **Objective:** Implement sidebar navigation and route-based views.
- **Affected Files:** `frontend/src/app/app.routes.ts`, `frontend/src/app/app.component.html`.
- **Acceptance Criteria:** User can navigate between `/models`, `/pipelines`, and `/playground`.

### Task 4.2: Dynamic Model Configuration UI
- **Objective:** Build a form that renders fields based on the selected Provider.
- **Affected Files:** `frontend/src/app/components/model-form.component.ts`.
- **Acceptance Criteria:** UI shows different fields for "OpenAI" vs "Ollama".

### Task 4.3: Knowledge Vault (Document Manager)
- **Objective:** Build the UI for uploading and managing indexed documents.
- **Affected Files:** `frontend/src/app/components/doc-manager.component.ts`.
- **Acceptance Criteria:** User can upload files and delete individual documents from a pipeline.

### Task 4.4: RAG Playground (Chat + Inspector)
- **Objective:** Implement split-screen chat with a "Source Inspector" panel.
- **Affected Files:** `frontend/src/app/components/chat-playground.component.ts`.
- **Acceptance Criteria:** Chat displays the answer on the left and retrieved chunks on the right.

---

## Epic 5: Production Hardening
*Goal: Scale and stabilize for production use.*

### Task 5.1: Async Indexing Job Queue
- **Objective:** Move indexing to background tasks with status polling.
- **Affected Files:** `backend/src/routers/rag.py`.
- **Acceptance Criteria:** Indexing returns a `job_id`; frontend polls for completion status.

### Task 5.2: RAG Hyperparameter Tuning
- **Objective:** Add `top_k`, `temperature`, and `system_prompt` to pipeline config.
- **Affected Files:** `backend/src/schemas/__init__.py`, `frontend/src/app/components/pipeline-config.component.ts`.
- **Acceptance Criteria:** Users can adjust retrieval depth and see the effect in the chat.

### Task 5.3: Document Deduplication (Hashing)
- **Objective:** Implement SHA-256 hashing to prevent duplicate indexing.
- **Affected Files:** `backend/src/services/chunking.py`, `backend/src/database.py`.
- **Acceptance Criteria:** Re-uploading the same file does not create duplicate chunks.
