"""
Pydantic schemas for the SLM Builder API.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

VectorStoreType = Literal["chroma", "mongodb"]


class ModelBase(BaseModel):
    name: str
    provider: str = "ollama"
    model_id: str
    description: Optional[str] = None
    is_active: bool = True


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Model(ModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PipelineBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_id: int
    vector_store_type: VectorStoreType = "chroma"
    vector_store_config: Optional[Dict[str, Any]] = None
    embedding_model: str = "local-hash"
    is_active: bool = True
    config: Optional[Dict[str, Any]] = None

    @field_validator("vector_store_config")
    @classmethod
    def validate_vector_store_config(
        cls, value: Optional[Dict[str, Any]], info
    ) -> Optional[Dict[str, Any]]:
        store_type = info.data.get("vector_store_type", "chroma")
        config = value or {}
        if store_type == "mongodb":
            required = ["uri", "database", "collection", "index_name"]
            missing = [field for field in required if not config.get(field)]
            if missing:
                missing_list = ", ".join(missing)
                raise ValueError(f"MongoDB vector store config missing: {missing_list}")
        return value


class PipelineCreate(PipelineBase):
    pass


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[int] = None
    vector_store_type: Optional[VectorStoreType] = None
    vector_store_config: Optional[Dict[str, Any]] = None
    embedding_model: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class Pipeline(PipelineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    indexing_status: str
    last_indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentBase(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pipeline_id: int
    source_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class RAGConfigBase(BaseModel):
    pipeline_id: int
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "local-hash"
    vector_store_type: VectorStoreType = "chroma"
    vector_store_config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class RAGConfigCreate(RAGConfigBase):
    pass


class RAGConfigUpdate(BaseModel):
    pipeline_id: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    embedding_model: Optional[str] = None
    vector_store_type: Optional[VectorStoreType] = None
    vector_store_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RAGConfig(RAGConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class IndexResponse(BaseModel):
    pipeline_id: int
    vector_store_type: VectorStoreType
    document_count: int
    chunk_count: int
    status: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    top_k: int = 4


class SourceChunk(BaseModel):
    document_id: int
    title: str
    text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]


class VectorStoreInfo(BaseModel):
    type: VectorStoreType
    label: str
    description: str
    required_config_fields: List[str]
    default: bool = False
