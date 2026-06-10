from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    jurisdiction: str = Field(default="central", description="central, state, or international")
    doc_type: Optional[str] = Field(default=None, description="tax_act, gst_circular, fema_regulation, etc.")
    top_k: int = Field(default=5, ge=1, le=20)
    alpha: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Hybrid search weight override")

class RetrievedDocument(BaseModel):
    id: str
    title: str
    content: str
    source_url: str
    doc_type: str
    jurisdiction: str
    section: Optional[str] = None
    metadata: Dict[str, Any]
    dense_score: float
    sparse_score: float
    hybrid_score: float
    rerank_score: Optional[float] = None

class RetrieveResponse(BaseModel):
    query: str
    results: List[RetrievedDocument]
    total_found: int
    retrieval_time_ms: float
    strategy: str = "hybrid_dense_sparse"

class IngestRequest(BaseModel):
    source_url: str
    title: str
    content: str
    doc_type: str
    jurisdiction: str = "central"
    metadata: Dict[str, Any] = {}
    effective_date: Optional[str] = None

class IngestResponse(BaseModel):
    status: str
    chunks_ingested: int
    document_id: str
