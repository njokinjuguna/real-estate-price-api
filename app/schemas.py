"""
Pydantic is a powerful Python library used for data validation and settings management
using Python type hints. It’s widely used in frameworks like FastAPI because it helps ensure
that data coming into (or out of) your application is structured, typed, and validated automatically.

"""

from pydantic import BaseModel,Field
from typing import Union

class PredictRequest(BaseModel):
    OverallQual: int = Field(..., ge=1, le=10)
    GrLivArea: Union[int, float]
    GarageCars: int
    TotalBsmtSF: Union[int, float]
    YearBuilt: int


class PredictResponse(BaseModel):
    predicted_price: float

class HealthResponse(BaseModel):
    status: str