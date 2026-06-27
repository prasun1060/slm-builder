"""Vector store adapters for Chroma and MongoDB."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class VectorChunk:
    id: str
    document_id: int
    title: str
    text: str
    embedding: list[float]


@dataclass
class SearchResult:
    document_id: int
    title: str
    text: str
    score: float


class VectorStore(Protocol):
    def upsert(self, pipeline_id: int, chunks: list[VectorChunk]) -> None:
        ...

    def search(
        self, pipeline_id: int, query_embedding: list[float], top_k: int
    ) -> list[SearchResult]:
        ...


class VectorStoreError(RuntimeError):
    pass


class ChromaVectorStore:
    def __init__(self, config: dict[str, Any] | None = None):
        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreError("ChromaDB is not installed. Run `uv sync`.") from exc

        config = config or {}
        persist_dir = config.get("persist_dir") or os.getenv(
            "CHROMA_PERSIST_DIR", "./data/chroma"
        )
        self.client = chromadb.PersistentClient(path=persist_dir)

    def _collection(self, pipeline_id: int):
        return self.client.get_or_create_collection(name=f"pipeline_{pipeline_id}")

    def upsert(self, pipeline_id: int, chunks: list[VectorChunk]) -> None:
        if not chunks:
            return
        collection = self._collection(pipeline_id)
        collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {"document_id": chunk.document_id, "title": chunk.title}
                for chunk in chunks
            ],
        )

    def search(
        self, pipeline_id: int, query_embedding: list[float], top_k: int
    ) -> list[SearchResult]:
        collection = self._collection(pipeline_id)
        result = collection.query(query_embeddings=[query_embedding], n_results=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        results: list[SearchResult] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            results.append(
                SearchResult(
                    document_id=int(metadata.get("document_id", 0)),
                    title=str(metadata.get("title", "Document")),
                    text=document,
                    score=1 / (1 + float(distance)),
                )
            )
        return results


class MongoVectorStore:
    def __init__(self, config: dict[str, Any] | None = None):
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise VectorStoreError("PyMongo is not installed. Run `uv sync`.") from exc

        config = config or {}
        uri = config.get("uri") or os.getenv("MONGODB_URI")
        database = config.get("database") or os.getenv("MONGODB_DATABASE")
        collection = config.get("collection") or os.getenv("MONGODB_COLLECTION")
        self.index_name = config.get("index_name") or os.getenv("MONGODB_VECTOR_INDEX")

        missing = [
            name
            for name, value in {
                "uri": uri,
                "database": database,
                "collection": collection,
                "index_name": self.index_name,
            }.items()
            if not value
        ]
        if missing:
            raise VectorStoreError(f"MongoDB vector store config missing: {', '.join(missing)}")

        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.collection = self.client[database][collection]

    def upsert(self, pipeline_id: int, chunks: list[VectorChunk]) -> None:
        for chunk in chunks:
            self.collection.update_one(
                {"_id": chunk.id},
                {
                    "$set": {
                        "pipeline_id": pipeline_id,
                        "document_id": chunk.document_id,
                        "title": chunk.title,
                        "text": chunk.text,
                        "embedding": chunk.embedding,
                    }
                },
                upsert=True,
            )

    def search(
        self, pipeline_id: int, query_embedding: list[float], top_k: int
    ) -> list[SearchResult]:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(top_k * 10, 20),
                    "limit": top_k,
                    "filter": {"pipeline_id": pipeline_id},
                }
            },
            {"$project": {"document_id": 1, "title": 1, "text": 1, "score": {"$meta": "vectorSearchScore"}}},
        ]
        try:
            docs = list(self.collection.aggregate(pipeline))
        except Exception as exc:
            raise VectorStoreError(f"MongoDB vector search failed: {exc}") from exc

        return [
            SearchResult(
                document_id=int(doc.get("document_id", 0)),
                title=str(doc.get("title", "Document")),
                text=str(doc.get("text", "")),
                score=float(doc.get("score", 0.0)),
            )
            for doc in docs
        ]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_length = math.sqrt(sum(a * a for a in left))
    right_length = math.sqrt(sum(b * b for b in right))
    if not left_length or not right_length:
        return 0.0
    return numerator / (left_length * right_length)


def get_vector_store(store_type: str, config: dict[str, Any] | None = None) -> VectorStore:
    if store_type == "chroma":
        return ChromaVectorStore(config)
    if store_type == "mongodb":
        return MongoVectorStore(config)
    raise VectorStoreError(f"Unsupported vector store: {store_type}")
