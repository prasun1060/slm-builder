import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.routers import rag
from main import app


client = TestClient(app)


class FakeVectorStore:
    chunks = []

    def upsert(self, pipeline_id, chunks):
        self.__class__.chunks = chunks

    def search(self, pipeline_id, query_embedding, top_k):
        from src.services.vector_stores import SearchResult

        return [
            SearchResult(
                document_id=1,
                title="Test document",
                text="SLM Builder creates local RAG pipelines.",
                score=0.9,
            )
        ]


def create_model():
    response = client.post(
        "/api/models/",
        json={
            "name": "Test Ollama",
            "provider": "ollama",
            "model_id": "llama3.2",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_pipeline(vector_store_type="chroma", vector_store_config=None):
    model = create_model()
    response = client.post(
        "/api/pipelines/",
        json={
            "name": "Test pipeline",
            "model_id": model["id"],
            "vector_store_type": vector_store_type,
            "vector_store_config": vector_store_config or {},
        },
    )
    return response


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_model_crud():
    model = create_model()
    response = client.get(f"/api/models/{model['id']}")
    assert response.status_code == 200
    assert response.json()["model_id"] == "llama3.2"


def test_pipeline_validates_mongodb_config():
    response = create_pipeline(vector_store_type="mongodb", vector_store_config={})
    assert response.status_code == 422
    assert "MongoDB vector store config missing" in response.text


def test_rag_indexing_with_fake_store(monkeypatch):
    monkeypatch.setattr(rag, "get_vector_store", lambda store_type, config: FakeVectorStore())
    pipeline = create_pipeline().json()

    document_response = client.post(
        f"/api/rag/pipelines/{pipeline['id']}/documents",
        json={
            "title": "Test document",
            "content": "SLM Builder creates local RAG pipelines from documents.",
        },
    )
    assert document_response.status_code == 201

    index_response = client.post(f"/api/rag/pipelines/{pipeline['id']}/index")
    assert index_response.status_code == 200
    assert index_response.json()["status"] == "indexed"
    assert index_response.json()["chunk_count"] > 0
