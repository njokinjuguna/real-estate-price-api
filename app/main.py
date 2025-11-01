import os
from fastapi import FastAPI, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from dotenv import load_dotenv

from app.schemas import PredictRequest, PredictResponse, HealthResponse
from app.security import verify_api_key
from app.inference import load_model, predict
from app.db import init_db, get_session
from app.crud import log_prediction

load_dotenv()

# ---------- Rate limit storage ----------
REDIS_URL = os.getenv("REDIS_URL")
STORAGE_URI = REDIS_URL if REDIS_URL else "memory://"

def key_func(request: Request):
    # Prefer API key; fallback to client IP
    return request.headers.get("api-key") or get_remote_address(request)

limiter = Limiter(key_func=key_func, storage_uri=STORAGE_URI)

app = FastAPI(title="AI Property Price API", version="0.1.0")
app.state.limiter = limiter
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",   # VS Code Live Server
        "http://localhost:5500",
        "https://your-widget-demo.vercel.app",  # after deploy
        "https://your-client-site.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------- Custom 429 with nice headers ----------
async def rate_limited_response(request: Request, exc: RateLimitExceeded):
    vrl = getattr(request.state, "view_rate_limit", None)  # populated by SlowAPI
    headers: dict[str, str] = {}
    body = {"detail": "Rate limit exceeded"}

    if vrl:
        # Standard-ish headers
        try:
            headers["X-RateLimit-Limit"] = str(vrl.limit.amount)
            headers["X-RateLimit-Period"] = vrl.limit.granularity  # e.g. "minute", "10 seconds"
        except Exception:
            pass

        headers["X-RateLimit-Remaining"] = "0"

        # Add Retry-After if we know when the bucket resets
        if getattr(vrl, "reset", None) and getattr(vrl, "now", None):
            retry_after = max(0, int((vrl.reset - vrl.now).total_seconds()))
            headers["Retry-After"] = str(retry_after)
            body["retry_after"] = retry_after

    return JSONResponse(status_code=429, content=body, headers=headers)

app.add_exception_handler(RateLimitExceeded, rate_limited_response)

# ---------- Add headers on successful responses too ----------
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    vrl = getattr(request.state, "view_rate_limit", None)
    if vrl:
        try:
            response.headers["X-RateLimit-Limit"] = str(vrl.limit.amount)
            response.headers["X-RateLimit-Period"] = vrl.limit.granularity
        except Exception:
            pass
        remaining = getattr(vrl, "remaining", 0)
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(remaining)))
        if remaining <= 0 and getattr(vrl, "reset", None) and getattr(vrl, "now", None):
            response.headers["Retry-After"] = str(int((vrl.reset - vrl.now).total_seconds()))
    return response

# ---------- Dynamic free/paid limits ----------
def tier_limit(request: Request | None = None) -> str:
    """
    Return the rate limit string. SlowAPI may probe without a Request; default to FREE_LIMIT then.
    """
    free = os.getenv("FREE_LIMIT", "30/minute")
    paid = os.getenv("PAID_LIMIT", "300/minute")
    if request is None:
        return free

    api_key = (request.headers.get("api-key") or "").strip()
    paid_keys = {k.strip() for k in os.getenv("PAID_KEYS", "").split(",") if k.strip()}
    return paid if api_key in paid_keys else free

# ---------- Startup ----------
@app.on_event("startup")
def startup():
    print(f"[rate-limit] storage_uri = {STORAGE_URI}")
    print(f"[rate-limit] paid keys = {os.getenv('PAID_KEYS')}")
    init_db()
    load_model()

# ---------- Routes ----------
@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
@limiter.limit(tier_limit)
def predict_price(
    payload: PredictRequest,
    request: Request,
    api_key: str | None = Header(default=None, alias="api-key"),
    session = Depends(get_session),
):
    verify_api_key(api_key)
    price = float(predict(payload.dict()))  # ensure JSON-serializable
    log_prediction(session, payload.dict(), price, api_key)
    return {"predicted_price": price}

@app.get("/me/usage")
def my_usage(
    request: Request,
    api_key: str | None = Header(default=None, alias="api-key"),
    session = Depends(get_session),
):
    verify_api_key(api_key)
    q = text("""
        SELECT COUNT(*)::int
        FROM prediction_logs
        WHERE api_key = :k
          AND date_trunc('month', created_at) = date_trunc('month', now())
    """)
    res = session.execute(q, {"k": api_key}).scalar()
    return {"api_key": api_key, "month_requests": int(res or 0)}

@app.get("/debug/limits")
def debug_limits(request: Request, api_key: str | None = Header(default=None, alias="api-key")):
    return {
        "api_key": api_key,
        "active_limit": tier_limit(request),
        "paid_keys": os.getenv("PAID_KEYS", "")
    }
