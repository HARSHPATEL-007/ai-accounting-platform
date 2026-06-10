from temporalio import activity
from shared.models import InvoiceToLedgerInput
import httpx
import structlog

logger = structlog.get_logger("workflow_engine")

@activity.defn
async def classify_document(document_id: str, s3_key: str) -> dict:
    """Activity: Classify document using OCR pipeline."""
    logger.info("activity_classify_start", document_id=document_id)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://ocr-pipeline:8000/classify",
                json={"document_id": document_id, "s3_key": s3_key},
                timeout=30.0
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("activity_classify_failed", document_id=document_id, error=str(e))
        raise activity.ApplicationError(f"Classification failed: {e}")

@activity.defn
async def extract_document_data(document_id: str, s3_key: str) -> dict:
    """Activity: Extract structured data from document."""
    logger.info("activity_extract_start", document_id=document_id)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://ocr-pipeline:8000/extract",
                json={"document_id": document_id, "s3_key": s3_key},
                timeout=60.0
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("activity_extract_failed", document_id=document_id, error=str(e))
        raise activity.ApplicationError(f"Extraction failed: {e}")

@activity.defn
async def validate_extracted_data(extracted_data: dict) -> dict:
    """Activity: Validate extracted data (GSTIN, HSN, amounts)."""
    logger.info("activity_validate_start", extracted_keys=list(extracted_data.keys()))
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://ocr-pipeline:8000/validate",
                json={"extracted_data": extracted_data},
                timeout=10.0
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("activity_validate_failed", error=str(e))
        raise activity.ApplicationError(f"Validation failed: {e}")

@activity.defn
async def create_ledger_entry(client_id: str, extracted_data: dict, document_id: str, created_by: str) -> dict:
    """Activity: Create double-entry ledger posting."""
    logger.info("activity_ledger_start", client_id=client_id, document_id=document_id)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://ledger-processor:8080/api/v1/ledgers",
                json={
                    "client_id": client_id,
                    "account_code": "PUR-001",  # Determined from doc type
                    "transaction_date": extracted_data.get("dates", [None])[0],
                    "transaction_type": "debit",
                    "amount": extracted_data.get("amounts", [{}])[0].get("value", 0),
                    "description": extracted_data.get("raw_text", "")[:200],
                    "gstin": extracted_data.get("gstin", [None])[0],
                    "hsn_code": extracted_data.get("hsn_codes", [None])[0],
                    "document_id": document_id,
                    "created_by": created_by
                },
                timeout=10.0
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("activity_ledger_failed", client_id=client_id, error=str(e))
        raise activity.ApplicationError(f"Ledger posting failed: {e}")

@activity.defn
async def reconcile_with_bank(client_id: str, ledger_entry_id: str, bank_tx_id: Optional[str] = None) -> dict:
    """Activity: Reconcile ledger entry with bank statement via Account Aggregator."""
    logger.info("activity_reconcile_start", client_id=client_id, ledger_entry_id=ledger_entry_id)
    # In production: call Account Aggregator API
    return {"status": "pending", "ledger_entry_id": ledger_entry_id, "matched": False}

@activity.defn
async def notify_human_review(document_id: str, reason: str) -> dict:
    """Activity: Flag for human-in-the-loop review."""
    logger.info("activity_hil_notification", document_id=document_id, reason=reason)
    # In production: send notification via notification-service
    return {"notified": True, "document_id": document_id, "reason": reason}
