from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/db.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Provider(Base):
    __tablename__ = "provider"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    config_schema = Column(JSON)

class Model(Base):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("provider.id"), index=True)
    model_id = Column(String, index=True)
    display_name = Column(String, index=True)
    config = Column(JSON)

class Pipeline(Base):
    __tablename__ = "pipeline"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    embedding_model_id = Column(Integer, ForeignKey("model.id"), index=True)
    generation_model_id = Column(Integer, ForeignKey("model.id"), index=True)
    vector_store_type = Column(String, index=True)
    vector_store_config = Column(JSON)
