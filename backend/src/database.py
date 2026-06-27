"""
Database configuration and models for SLM Builder.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable, default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/slm_builder.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    provider = Column(String)  # e.g., 'ollama', 'openrouter', 'huggingface'
    model_id = Column(String)  # The actual model ID from the provider
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pipelines = relationship("Pipeline", back_populates="model")

class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    vector_store_type = Column(String, default="chroma")
    vector_store_config = Column(JSON, nullable=True)
    embedding_model = Column(String, default="local-hash")
    is_active = Column(Boolean, default=True)
    indexing_status = Column(String, default="not_indexed")
    last_indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Pipeline configuration as JSON (steps, configurations, etc.)
    config = Column(JSON, nullable=True)

    # Relationships
    model = relationship("Model", back_populates="pipelines")
    rag_configs = relationship("RAGConfig", back_populates="pipeline")
    documents = relationship("Document", back_populates="pipeline", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    title = Column(String, index=True)
    content = Column(Text)
    source_type = Column(String, default="text")
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pipeline = relationship("Pipeline", back_populates="documents")

class RAGConfig(Base):
    __tablename__ = "rag_configs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    embedding_model = Column(String)  # e.g., 'sentence-transformers/all-MiniLM-L6-v2'
    vector_store_type = Column(String)  # e.g., 'chroma', 'mongodb'
    vector_store_config = Column(JSON, nullable=True)  # Configuration for the vector store
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pipeline = relationship("Pipeline", back_populates="rag_configs")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
