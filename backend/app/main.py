
from fastapi import FastAPI

from app.api.documents import router as documents_router

app = FastAPI(
    title="Automated Invoice Processing System",
    description="API for invoice upload, extraction, validation, and management.",
    version="0.1.0",
)

app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "Automated Invoice Processing API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
