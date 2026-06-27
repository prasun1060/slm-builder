"""Vector store capability endpoint."""

from fastapi import APIRouter

from ..schemas import VectorStoreInfo

router = APIRouter()


@router.get("/", response_model=list[VectorStoreInfo])
def list_vector_stores():
    return [
        VectorStoreInfo(
            type="chroma",
            label="Chroma",
            description="Local persistent vector database stored on disk.",
            required_config_fields=[],
            default=True,
        ),
        VectorStoreInfo(
            type="mongodb",
            label="MongoDB Atlas Vector Search",
            description="MongoDB collection with a configured vector search index.",
            required_config_fields=["uri", "database", "collection", "index_name"],
        ),
    ]
