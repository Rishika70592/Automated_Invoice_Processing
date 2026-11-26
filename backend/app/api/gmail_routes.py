
import os
import secrets

from fastapi import APIRouter, Header, HTTPException

from app.services.gmail_invoice_service import (
    process_gmail_invoices
)

router = APIRouter(
    prefix="/gmail",
    tags=["Gmail Ingestion"]
)


@router.post("/process-invoices")
def process_invoices(
    max_results: int = 20,
    x_api_key: str = Header(default=None)
):

    expected_key = os.getenv("GMAIL_INGESTION_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Gmail API key is not configured"
        )

    if not x_api_key or not secrets.compare_digest(
        x_api_key, expected_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    if not 1 <= max_results <= 100:
        raise HTTPException(
            status_code=400,
            detail="max_results must be between 1 and 100"
        )

    try:
        return process_gmail_invoices(max_results)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
