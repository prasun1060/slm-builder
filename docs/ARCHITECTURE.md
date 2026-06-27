# SLM Builder Architecture Specification

## 1. Core Philosophy
- **Local-First:** Prioritize local runtimes (Ollama, llama.cpp).
- **Provider Agnostic:** Core logic must not depend on specific LLM or Vector DB implementations.
- **Modular Workflow:** RAG is treated as a sequence of interchangeable nodes (DAG), not a hardcoded pipeline.
- **State-Driven:** Long-running tasks (indexing) are managed via state transitions, not synchronous HTTP requests.

## 2. High-Level Component Diagram
`Frontend (Angular)` $\rightarrow$ `API (FastAPI)` $\rightarrow$ `Orchestrator` $\rightarrow$ `Adapters` $\rightarrow$ `External Providers`

## 3. Domain Model & Data Layer
### 3.1 Metadata Store (SQLite/SQLAlchemy)
- **Providers:** `id, name, type (LOCAL|CLOUD), config_schema (JSON)`
- **Models:** `id, provider_id, model_id, display_name, config (JSON)`
- **Pipelines:** `id, name, embedding_model_id, generation_model_id, vector_store_id, hyperparameters (JSON)`
- **Documents:** `id, pipeline_id, filename, hash, status (PENDING|INDEXED|FAILED)`

### 3.2 Vector Store Abstraction
All vector stores must implement the `IVectorStore` interface:
- `upsert(documents: List[Chunk])`
- `query(vector: List[float], top_k: int) -> List[Chunk]`
- `delete(document_id: str)`
- `clear_collection()`

## 4. Backend Architecture (Clean Architecture)
### 4.1 Layers
- **API Layer (`/routers`):** Handles HTTP, request validation (Pydantic), and response formatting.
- **Service Layer (`/services`):** Orchestrates business logic. No provider-specific code here.
- **Adapter Layer (`/adapters`):** Translates generic service calls into provider-specific API calls (e.g., `OllamaAdapter`, `ChromaAdapter`).
- **Infrastructure Layer:** Database connections, file system access.

### 4.2 The RAG Workflow (Node-Based)
The `RAGOrchestrator` executes a sequence of steps:
1. **Query Transformation:** (Optional) Rewrite user query.
2. **Retrieval:** Call `IVectorStore.query()` using the pipeline's `EmbeddingModel`.
3. **Augmentation:** Combine retrieved chunks into a prompt template.
4. **Generation:** Call `ILLMProvider.generate()` using the pipeline's `GenerationModel`.

## 5. Frontend Architecture (Angular)
- **State Management:** Use a service-based store to track active pipelines and model configurations.
- **Dynamic UI:** 
    - `ProviderForm`: Renders fields based on the `config_schema` provided by the backend.
    - `ChatPlayground`: Split-view (Chat $\mid$ Source Inspector).
- **Routing:** `/models`, `/pipelines`, `/knowledge-vault`, `/playground`.

## 6. Extensibility & Future-Proofing
- **Adding a New LLM:** Implement `ILLMProvider` $\rightarrow$ Register in `providers` table.
- **Adding a New Vector DB:** Implement `IVectorStore` $\rightarrow$ Register in `vector_store_types`.
- **Agent Support:** The Node-based workflow allows adding "Tool" nodes (e.g., Web Search, Python Interpreter) to the DAG.

## 7. Critical Constraints for AI Agents
- **No Provider Leakage:** Never use provider-specific types (e.g., `chromadb.Collection`) in the Service layer.
- **Async First:** All indexing operations must be background tasks.
- **Strict Typing:** Use Pydantic models for all data crossing layer boundaries.
