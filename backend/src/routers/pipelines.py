"""Router for RAG pipeline management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src import database as db_models
from src import schemas
from src.database import get_db
from src.services import IVectorStore

router = APIRouter()


def _ensure_model_exists(db: Session, model_id: int) -> None:
    exists = db.query(db_models.Model).filter(db_models.Model.id == model_id).first()
    if exists is None:
        raise HTTPException(status_code=400, detail="Model does not exist")


@router.post("/", response_model=schemas.Pipeline, status_code=status.HTTP_201_CREATED)
def create_pipeline(pipeline: schemas.PipelineCreate, db: Session = Depends(get_db)):
    _ensure_model_exists(db, pipeline.embedding_model_id)
    _ensure_model_exists(db, pipeline.generation_model_id)
    db_pipeline = db_models.Pipeline(**pipeline.model_dump())
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


@router.get("/", response_model=list[schemas.Pipeline])
def read_pipelines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(db_models.Pipeline).offset(skip).limit(limit).all()


@router.get("/{pipeline_id}", response_model=schemas.Pipeline)
def read_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    pipeline = (
        db.query(db_models.Pipeline).filter(db_models.Pipeline.id == pipeline_id).first()
    )
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.put("/{pipeline_id}", response_model=schemas.Pipeline)
def update_pipeline(
    pipeline_id: int, update: schemas.PipelineUpdate, db: Session = Depends(get_db)
):
    db_pipeline = (
        db.query(db_models.Pipeline).filter(db_models.Pipeline.id == pipeline_id).first()
    )
    if db_pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    update_data = update.model_dump(exclude_unset=True)
    if "embedding_model_id" in update_data:
        _ensure_model_exists(db, update_data["embedding_model_id"])
    if "generation_model_id" in update_data:
        _ensure_model_exists(db, update_data["generation_model_id"])

    vector_store_type = update_data.get("vector_store_type", db_pipeline.vector_store_type)
    vector_store_config = update_data.get(
        "vector_store_config", db_pipeline.vector_store_config
    )
    if vector_store_type == "mongodb":
        required = ["uri", "database", "collection", "index_name"]
        missing = [field for field in required if not (vector_store_config or {}).get(field)]
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"MongoDB vector store config missing: {', '.join(missing)}",
            )

    for key, value in update_data.items():
        setattr(db_pipeline, key, value)

    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    db_pipeline = (
        db.query(db_models.Pipeline).filter(db_models.Pipeline.id == pipeline_id).first()
    )
    if db_pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    db.delete(db_pipeline)
    db.commit()
    return None

@router.get("/vector-stores", response_model=list[IVectorStore])
def list_vector_stores():
    return [
        IVectorStore(
            type="chroma",
            label="Chroma",
            description="Local persistent vector database stored on disk.",
            required_config_fields=[],
            default=True,
        ),
        IVectorStore(
            type="mongodb",
            label="MongoDB Atlas Vector Search",
            description="MongoDB collection with a configured vector search index.",
            required_config_fields=["uri", "database", "collection", "index_name"],
        ),
    ]
