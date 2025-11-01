import os
from fastapi import HTTPException, status

def verify_api_key(api_key: str | None):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    free_key = os.getenv("API_KEY", "").strip()
    paid_keys = {k.strip() for k in os.getenv("PAID_KEYS", "").split(",") if k.strip()}
    allowed = {free_key} | paid_keys if free_key else paid_keys

    if api_key not in allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
