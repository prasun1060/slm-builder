from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Type
from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    index: int

# --- Provider Config Schemas ---
class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    timeout: int = 30

class OpenAIConfig(BaseModel):
    api_key: str
    organization_id: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"

class AnthropicConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.anthropic.com"

CONFIG_REGISTRY: Dict[str, Type[BaseModel]] = {
    "ollama": OllamaConfig,
    "openai": OpenAIConfig,
    "anthropic": AnthropicConfig,
}

# --- Core Schemas ---
class ProviderBase(BaseModel):
    name: str
    type: str
    config_schema: Optional[Dict[str, Any]] = None

class ProviderCreate(ProviderBase):
    pass

class Provider(ProviderBase):
    id: int
    class Config:
        from_attributes = True

class ModelBase(BaseModel):
    display_name: str
    model_id: str
    provider_id: int
    config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    model_id: Optional[str] = None
    provider_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class Model(ModelBase):
    id: int
    class Config:
        from_attributes = True

class ProviderConfig(BaseModel):
    required_keys: List[str]

class ProviderInfo(BaseModel):
    name: str
    description: str
    config: ProviderConfig

class PipelineBase(BaseModel):
    name: str
    embedding_model_id: int
    generation_model_id: int
    vector_store_type: str
    vector_store_config: Dict[str, Any] = Field(default_factory=dict)

class PipelineCreate(PipelineBase):
    pass

class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    embedding_model_id: Optional[int] = None
    generation_model_id: Optional[int] = None
    vector_store_type: Optional[str] = None
    vector_store_config: Optional[Dict[str, Any]] = None

class Pipeline(PipelineBase):
    id: int
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    top_k: int = 3

class SourceChunk(BaseModel):
    document_id: str
    title: str
    text: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
