# System Architecture: SLM Builder Backend

## High-Level Overview
The backend is a FastAPI application designed to orchestrate Small Language Models (SLMs) and Retrieval Augmented Generation (RAG) pipelines. It allows users to manage LLM providers, specific models, and RAG pipelines that combine a specific embedding model, generation model, and vector store.

## Component Breakdown

### 1. API Layer (`backend/src/routers/`)
- **`models.py`**: CRUD operations for LLM models.
- **`pipelines.py`**: CRUD operations for RAG pipelines and vector store configuration.
- **`rag.py`**: The execution engine. It takes a `pipeline_id`, initializes the necessary services, and handles the chat loop.

### 2. Service Layer (`backend/src/services/`)
- **`OllamaService`**: An asynchronous client using `httpx` to communicate with the Ollama API for generating embeddings and text responses.
- **`VectorStoreFactory` & Adapters**: Implements the Adapter Pattern to provide a unified interface (`IVectorStore`) for different vector databases:
    - `ChromaAdapter`: Local vector storage.
    - `MongoDBAdapter`: Cloud-based vector search using MongoDB Atlas `$vectorSearch`.
- **`RAGOrchestrator`**: The coordinator. It manages the sequence:
    1. Generate query embedding via `OllamaService`.
    2. Retrieve relevant chunks via `IVectorStore`.
    3. Construct a context-aware prompt.
    4. Generate the final answer via `OllamaService`.
- **`chunking.py`**: Utility for splitting documents into manageable chunks.

### 3. Data Layer (`backend/src/database.py`)
- **SQLAlchemy Models**:
    - `Provider`: LLM providers (e.g., Ollama, OpenAI).
    - `Model`: Specific model versions linked to a provider.
    - `Pipeline`: Configuration linking an embedding model, generation model, and vector store.

## Data Flow (RAG Query)
`User Request` $\rightarrow$ `rag.py` $\rightarrow$ `RAGOrchestrator` $\rightarrow$ `OllamaService (Embedding)` $\rightarrow$ `IVectorStore (Query)` $\rightarrow$ `OllamaService (Generation)` $\rightarrow$ `User Response`

## Frontend Architecture (Angular)
- **Framework**: Angular 18+ (Standalone Components, Signals)
- **Entry Point**: `frontend/src/app/app.component.ts` (Single component MVP)
- **State Management**: Service-based store (`ModelService`, `PipelineService`, `ChatService`)
- **UI Components**:
    - **Model Management**: List/Create/Delete models.
    - **Pipeline Builder**: Select embedding/generation models + vector store config.
    - **Chat Playground**: Split view (Chat History | Source Inspector).
- **API Integration**: Typed HTTP clients consuming backend Pydantic schemas (`Model`, `Pipeline`, `ChatRequest`, `ChatResponse`).

## Design Principles
- **Asynchronous I/O**: All network-bound operations (LLM calls, DB queries) use `async/await` to prevent event-loop blocking.
- **Interface-Based Design**: Vector stores are accessed via the `IVectorStore` interface, allowing new databases to be added without changing the orchestrator.
- **Schema Separation**: Strict separation between SQLAlchemy models (database) and Pydantic models (API) to ensure data integrity.
- **Contract First**: Backend Pydantic schemas are the single source of truth for Frontend TypeScript interfaces.
