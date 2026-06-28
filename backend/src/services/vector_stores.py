from typing import List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from abc import ABC, abstractmethod
from src.schemas.schemas import Chunk  # Import Chunk

class IVectorStore(ABC):
    @abstractmethod
    def upsert(self, chunks: List[Chunk]) -> None:
        pass

    @abstractmethod
    def query(self, vector: List[float], top_k: int) -> List[Chunk]:
        pass

    @abstractmethod
    def delete(self, document_id: str):
        pass

    @abstractmethod
    def clear_collection(self):
        pass

class ChromaAdapter(IVectorStore):
    def __init__(self, vector_store_config: dict):
        self.vector_store_config = vector_store_config

    def query(self, vector: List[float], top_k: int) -> List[Chunk]:
        # Assuming vector_store_config contains the necessary details to connect to Chroma
        # This is a placeholder implementation
        chunks = []
        for i in range(top_k):
            chunks.append(Chunk(text=f"Document {i}", index=i))
        return chunks

class MongoDBAdapter(IVectorStore):
    def __init__(self, uri: str, database_name: str, collection_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def query(self, vector: List[float], top_k: int) -> List[Chunk]:
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "vector": vector,
                        "k": top_k,
                        "path": "vector",
                        "distance": "cosine"
                    }
                }
            ]
            results = self.collection.aggregate(pipeline)
            chunks = []
            for i, result in enumerate(results):
                chunks.append(Chunk(text=result["text"], index=i))
            return chunks
        except PyMongoError as e:
            raise ValueError(f"MongoDB query failed: {e}") from e

class VectorStoreFactory:
    @staticmethod
    def get_store(vector_store_type: str, vector_store_config: dict) -> IVectorStore:
        if vector_store_type == "chroma":
            return ChromaAdapter(vector_store_config)
        elif vector_store_type == "mongodb":
            return MongoDBAdapter(vector_store_config["uri"], vector_store_config["database_name"], vector_store_config["collection_name"])
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")
