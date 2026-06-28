from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src import schemas
from src.database import get_db, Pipeline, Model  # Import Model
from src.services.rag_orchestrator import RAGOrchestrator
from src.services.ollama import OllamaService
from src.services.vector_stores import IVectorStore, VectorStoreFactory  # Import VectorStoreFactory

router = APIRouter()

@router.post("/pipelines/{pipeline_id}/chat", response_model=schemas.ChatResponse)
async def chat_with_pipeline(
    pipeline_id: int, request: schemas.ChatRequest, db: Session = Depends(get_db)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    model = db.query(Model).filter(Model.id == pipeline.generation_model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    vector_store = VectorStoreFactory.get_store(
        pipeline.vector_store_type,
        pipeline.vector_store_config,
    )
    ollama_service = OllamaService(model_config=model.config)

    rag_orchestrator = RAGOrchestrator(vector_store, ollama_service)

    try:
        response = await rag_orchestrator.query_pipeline(pipeline_id, request.message, request.top_k)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
