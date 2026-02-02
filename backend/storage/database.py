from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./robotcem.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DesignJob(Base):
    __tablename__ = "design_jobs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    prompt = Column(String)
    status = Column(String)  # queued, processing, completed, failed
    progress = Column(Integer, default=0)
    specification = Column(JSON)
    validation = Column(JSON)
    stl_path = Column(String, nullable=True)
    bom = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ComponentCache(Base):
    __tablename__ = "component_cache"
    
    mpn = Column(String, primary_key=True, index=True)
    data = Column(JSON)
    price = Column(Float)
    stock = Column(Integer)
    supplier = Column(String)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class MaterialPricing(Base):
    __tablename__ = "material_pricing"
    
    material = Column(String, primary_key=True, index=True)
    price_per_kg = Column(Float)
    availability = Column(String)
    supplier = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
