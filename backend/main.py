"""SLM Builder FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import models, pipelines, rag, vector_stores
from src.database import engine, Base

os.makedirs("./data", exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SLM Builder API",
    description="Backend API for SLM Builder - A drag-and-drop interface for building Small Language Models",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(vector_stores.router, prefix="/api/vector-stores", tags=["vector-stores"])

@app.get("/")
async def root():
    return {"message": "Welcome to SLM Builder API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
