# SLM Builder

SLM Builder is a local-first RAG builder MVP. It pairs an Angular UI with a FastAPI backend so a user can register an Ollama model, create a RAG pipeline, add knowledge documents, choose a vector database, index content, and test chat.

## Current MVP

- Backend: FastAPI, SQLAlchemy, SQLite metadata, `uv` dependency management.
- Frontend: Angular standalone app.
- Model runtime: Ollama.
- Vector stores: Chroma by default, MongoDB Atlas Vector Search when configured.
- Documents: pasted text plus `.txt` and `.md` upload.

## Run Backend

```powershell
cd backend
uv sync
uv run uvicorn main:app --reload
```

The API runs on `http://localhost:8000` by default.

## Run Frontend

```powershell
cd frontend
npm install
npm start
```

The UI runs on `http://localhost:4200` and calls the API at `http://localhost:8000`.

## Useful API Endpoints

- `GET /health`
- `GET /api/vector-stores`
- `GET/POST /api/models`
- `GET/POST /api/pipelines`
- `POST /api/rag/pipelines/{pipeline_id}/documents`
- `POST /api/rag/pipelines/{pipeline_id}/upload`
- `POST /api/rag/pipelines/{pipeline_id}/index`
- `POST /api/rag/pipelines/{pipeline_id}/chat`

## Notes For Aider

- Backend database models live in `backend/app/database.py`.
- API schemas live in `backend/app/schemas/__init__.py`.
- Routers live in `backend/app/routers/`.
- RAG behavior is in `backend/app/services/`.
- Frontend app code is concentrated in `frontend/src/app/app.component.*` for the MVP.
- Add new vector databases by implementing the same adapter shape used in `backend/app/services/vector_stores.py`.
