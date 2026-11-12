
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.documents import router as documents_router
from app.api.invoices import router as invoices_router
app = FastAPI(
    title="Automated Invoice Processing System",
    description="API for invoice upload, extraction, validation, and management.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router)

app.include_router(invoices_router)
@app.get("/")
def root():
    return {
        "message": "Automated Invoice Processing API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
