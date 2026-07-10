from fastapi import FastAPI

from app import models
from app.database import Base, engine

app = FastAPI(
    title="Duolingo Clone API",
    description="Backend API for Duolingo Clone",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "Duolingo Clone Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected"
    }