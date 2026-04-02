from fastapi import FastAPI
from app.api.routers import jobs, overrides, admin
from app.api.middleware import RateLimitMiddleware

app = FastAPI(title="Compliance Analysis Agent", version="0.1.0")
app.add_middleware(RateLimitMiddleware)
app.include_router(jobs.router)
app.include_router(overrides.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
