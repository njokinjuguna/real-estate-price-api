from sqlalchemy.orm import Session
from app.models import PredictionLog

def log_prediction(session: Session, features: dict, price: float,api_key: str | None):
    row = PredictionLog(features=features, predicted_price=price,api_key=api_key)
    session.add(row)
    session.commit()