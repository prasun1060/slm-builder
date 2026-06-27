# SLM Builder Backend

FastAPI backend for the SLM Builder RAG MVP.

## Setup

```powershell
uv sync
uv run uvicorn main:app --reload
uv run pytest
```

## Environment

- `DATABASE_URL`: SQLAlchemy database URL. Defaults to `sqlite:///./data/slm_builder.db`.
- `OLLAMA_BASE_URL`: Ollama server URL. Defaults to `http://localhost:11434`.
- `CHROMA_PERSIST_DIR`: Chroma persistence path. Defaults to `./data/chroma`.
- `MONGODB_URI`: MongoDB connection string.
- `MONGODB_DATABASE`: MongoDB database name.
- `MONGODB_COLLECTION`: MongoDB collection name.
- `MONGODB_VECTOR_INDEX`: MongoDB Atlas vector search index name.

MongoDB settings can also be stored per pipeline in `vector_store_config`.

## Architecture

- `main.py` creates the FastAPI app and includes routers.
- `app/database.py` contains SQLAlchemy models and the database session dependency.
- `app/schemas/__init__.py` contains API request and response models.
- `app/routers/models.py` manages Ollama model records.
- `app/routers/pipelines.py` manages RAG pipelines and vector store choice.
- `app/routers/rag.py` handles document ingestion, indexing, and chat.
- `app/services/vector_stores.py` hides Chroma/MongoDB differences behind one adapter API.
- `app/services/embeddings.py` currently uses deterministic hash embeddings so the MVP indexes locally without a remote embedding model.

## Extension Points

- Replace `HashEmbeddingService` with sentence-transformers or provider embeddings when quality matters.
- Add model providers by extending the model schema/router and adding provider-specific generation clients.
- Add vector databases by implementing `upsert` and `search` in a new adapter and extending `get_vector_store`.
