"""RAG document, indexing, and chat endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import database as db_models
from .. import schemas
from ..database import get_db
from ..services.chunking import chunk_text
from ..services.embeddings import embedding_service
from ..services.ollama import OllamaUnavailableError, generate_answer
from ..services.vector_stores import VectorChunk, VectorStoreError, get_vector_store

router = APIRouter()


def _get_pipeline(db: Session, pipeline_id: int) -> db_models.Pipeline:
    pipeline = (
        db.query(db_models.Pipeline).filter(db_models.Pipeline.id == pipeline_id).first()
    )
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post(
    "/pipelines/{pipeline_id}/documents",
    response_model=schemas.Document,
    status_code=status.HTTP_201_CREATED,
)
def add_document(
    pipeline_id: int, document: schemas.DocumentCreate, db: Session = Depends(get_db)
):
    _get_pipeline(db, pipeline_id)
    db_document = db_models.Document(
        pipeline_id=pipeline_id,
        title=document.title,
        content=document.content,
        source_type="text",
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.post(
    "/pipelines/{pipeline_id}/upload",
    response_model=schemas.Document,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    pipeline_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    _get_pipeline(db, pipeline_id)
    if not file.filename or not file.filename.lower().endswith((".txt", ".md")):
        raise HTTPException(status_code=400, detail="Only .txt and .md files are supported")

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text") from exc

    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty")

    db_document = db_models.Document(
        pipeline_id=pipeline_id,
        title=file.filename,
        content=content,
        source_type="upload",
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.post("/pipelines/{pipeline_id}/index", response_model=schemas.IndexResponse)
def index_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    pipeline = _get_pipeline(db, pipeline_id)
    documents = (
        db.query(db_models.Document)
        .filter(db_models.Document.pipeline_id == pipeline_id)
        .all()
    )
    if not documents:
        raise HTTPException(status_code=400, detail="Pipeline has no documents to index")

    all_chunks: list[VectorChunk] = []
    for document in documents:
        chunks = chunk_text(document.content)
        document.chunk_count = len(chunks)
        embeddings = embedding_service.embed_many([chunk.text for chunk in chunks])
        for chunk, embedding in zip(chunks, embeddings):
            all_chunks.append(
                VectorChunk(
                    id=f"{pipeline_id}:{document.id}:{chunk.index}",
                    document_id=document.id,
                    title=document.title,
                    text=chunk.text,
                    embedding=embedding,
                )
            )

    try:
        store = get_vector_store(pipeline.vector_store_type, pipeline.vector_store_config)
        store.upsert(pipeline_id, all_chunks)
    except VectorStoreError as exc:
        pipeline.indexing_status = "failed"
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    pipeline.indexing_status = "indexed"
    pipeline.last_indexed_at = datetime.utcnow()
    db.commit()

    return schemas.IndexResponse(
        pipeline_id=pipeline_id,
        vector_store_type=pipeline.vector_store_type,
        document_count=len(documents),
        chunk_count=len(all_chunks),
        status=pipeline.indexing_status,
    )


@router.post("/pipelines/{pipeline_id}/chat", response_model=schemas.ChatResponse)
async def chat_with_pipeline(
    pipeline_id: int, request: schemas.ChatRequest, db: Session = Depends(get_db)
):
    pipeline = _get_pipeline(db, pipeline_id)
    if pipeline.indexing_status != "indexed":
        raise HTTPException(status_code=400, detail="Pipeline has not been indexed")
    if pipeline.model is None:
        raise HTTPException(status_code=400, detail="Pipeline has no model")

    query_embedding = embedding_service.embed(request.message)
    try:
        store = get_vector_store(pipeline.vector_store_type, pipeline.vector_store_config)
        results = store.search(pipeline_id, query_embedding, request.top_k)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not results:
        raise HTTPException(status_code=400, detail="No indexed context found")

    context = "\n\n".join(result.text for result in results)
    try:
        answer = await generate_answer(pipeline.model.model_id, request.message, context)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"Ollama unavailable: {exc}") from exc

    return schemas.ChatResponse(
        answer=answer,
        sources=[
            schemas.SourceChunk(
                document_id=result.document_id,
                title=result.title,
                text=result.text,
                score=result.score,
            )
            for result in results
        ],
    )
