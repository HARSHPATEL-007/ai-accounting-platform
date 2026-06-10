from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

class IntentType(str, Enum):
    GENERATE_CMA = "generate_cma"
    FEMA_ADVISORY = "fema_advisory"
    ESOP_VALUATION = "esop_valuation"
    GST_RECONCILIATION = "gst_reconciliation"
    AUDIT_QUERY = "audit_query"
    GENERAL_CHAT = "general_chat"
    TAX_ADVISORY = "tax_advisory"
    DOCUMENT_ANALYSIS = "document_analysis"
    TRANSFER_PRICING = "transfer_pricing"
    UNKNOWN = "unknown"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AgentState(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    intent: Optional[IntentType] = None
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    client_id: Optional[str] = None
    user_id: Optional[str] = None
    query: str = ""
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    tools_called: List[str] = Field(default_factory=list)
    calculation_results: Optional[Dict[str, Any]] = None
    draft_response: Optional[str] = None
    final_response: Optional[str] = None
    citations: List[Dict[str, str]] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    requires_human_review: bool = False
    human_review_reason: Optional[str] = None
    execution_trace_id: str = ""

class RouterOutput(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    target_agent: str

class Citation(BaseModel):
    source_url: str
    document_title: str
    section: Optional[str] = None
    excerpt: str
