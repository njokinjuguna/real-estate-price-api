import os
import joblib
import pandas as pd
_MODEL=None
def load_model():
    """Try to load a trained pipeline if present; otherwise stay in stub mode."""
    global _MODEL
    path=os.getenv("MODEL_PATH","model/pipeline.joblib")
    if os.path.exists(path):
        MODEL=joblib.load(path)
def predict(features:dict)-> float:
    """
    If a model is loaded, run a real prediction.
    Otherwise, return a simple heuristic so the endpoint works now.
    """
    global _MODEL
    if _MODEL is None:
        base = 50000
        score = (
                base
                + features.get("OverallQual", 5) * 15000
                + features.get("GrLivArea", 1000) * 90
                + features.get("GarageCars", 1) * 8000
                + features.get("TotalBsmtSF", 500) * 40
                + max(0, features.get("YearBuilt", 1990) - 1970) * 800
        )
        return float(score)

        X=pd.DataFrame([features])
        yhat=_MODEL.predict(X)[0]
        return float(yhat)