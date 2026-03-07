from fastapi import FastAPI
from app.db.database import engine
from app.db.models import Base
from app.api.v1.router import router as v1_router

app = FastAPI(title="Flow Mind - AI Workflow Engine", version="1.0.0")

# Database setup - create tables if not not exist
Base.metadata.create_all(bind=engine)

# register API routes
app.include_router(v1_router, prefix="/api/v1")
