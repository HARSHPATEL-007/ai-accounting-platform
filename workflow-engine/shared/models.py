from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class WorkflowType(str, Enum):
    INVOICE_TO_LEDGER = "invoice_to_ledger"
    CMA_GENERATION = "cma_generation"
    TAX_FILING = "tax_filing"
    ESOP_VALUATION = "esop_valuation"
    GST_RECONCILIATION = "gst_reconciliation"

class WorkflowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPENSATING = "compensating"

class InvoiceToLedgerInput(BaseModel):
    client_id: str
    document_id: str
    s3_key: str
    uploaded_by: str
    auto_post: bool = False

class InvoiceToLedgerResult(BaseModel):
    workflow_id: str
    run_id: str
    status: WorkflowStatus
    document_id: str
    extracted_data: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    ledger_entry_id: Optional[str] = None
    reconciliation_status: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps_completed: List[str] = []
