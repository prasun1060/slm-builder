from typing import List
from src.schemas.schemas import ChatResponse, SourceChunk
from .ollama import OllamaService
from .vector_stores import IVectorStore

class RAGOrchestrator:
    def __init__(self, vector_store: IVectorStore, ollama_service: OllamaService):
        self.vector_store = vector_store
        self.ollama_service: OllamaService = ollama_service

    async def query_pipeline(self, pipeline_id: int, message: str, top_k: int) -> ChatResponse:
        # Get embedding from OllamaService
        user_vector = await self.ollama_service.get_embedding(message)

        # Query the vector store for top-K chunks
        chunks = self.vector_store.query(user_vector, top_k)

        # Build the prompt
        prompt = f"Use the following context to answer: {chunks} \n\n Question: {message}"

        # Generate answer via OllamaService
        answer = await self.ollama_service.generate(prompt)

        # Map chunks to SourceChunk objects
        sources = [
            SourceChunk(
                document_id=str(chunk.index),
                title="Source",
                text=chunk.text,
                score=0.0
            )
            for chunk in chunks
        ]

        return ChatResponse(answer=answer, sources=sources)
