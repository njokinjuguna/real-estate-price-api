"""
SQLAlchemy ORM model that maps a Python class to a database table for logging predictions
"""

from sqlalchemy import Column, Integer, JSON, Float, DateTime, func,String
from sqlalchemy.orm import declarative_base

Base=declarative_base()
class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id=Column(Integer,primary_key=True)
    features=Column(JSON,nullable=False)
    predicted_price=Column(Float, nullable=False)
    api_key = Column(String, nullable=True)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
