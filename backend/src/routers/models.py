"""Router for model management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from .. import database as db_models
from ..database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Model, status_code=status.HTTP_201_CREATED)
def create_model(model: schemas.ModelCreate, db: Session = Depends(get_db)):
    db_model = db_models.Model(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


@router.get("/", response_model=list[schemas.Model])
def read_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(db_models.Model).offset(skip).limit(limit).all()


@router.get("/{model_id}", response_model=schemas.Model)
def read_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(db_models.Model).filter(db_models.Model.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=schemas.Model)
def update_model(
    model_id: int, model: schemas.ModelUpdate, db: Session = Depends(get_db)
):
    db_model = db.query(db_models.Model).filter(db_models.Model.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    for key, value in model.model_dump(exclude_unset=True).items():
        setattr(db_model, key, value)

    db.commit()
    db.refresh(db_model)
    return db_model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    db_model = db.query(db_models.Model).filter(db_models.Model.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    db.delete(db_model)
    db.commit()
    return None
