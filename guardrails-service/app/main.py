from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.guardrails.pii_guard import PIIGuard
from app.guardrails.topical_guard import TopicalGuard
from app.guardrails.hallucination_guard import HallucinationGuard
from app.guardrails.execution_guard import ExecutionGuard

app = FastAPI(title="Guardrails Service", version="1.0.0")

pii_guard = PIIGuard()
topical_guard = TopicalGuard()
hallucination_guard = HallucinationGuard()
execution_guard = ExecutionGuard()

class GuardrailsRequest(BaseModel):
    query: str = Field(..., max_length=5000)
    response: Optional[str] = None
    context: Optional[List[Dict[str, Any]]] = None
    intent: Optional[str] = None
    client_id: Optional[str] = None

class GuardrailsResponse(BaseModel):
    passed: bool
    layer: str
    reason: Optional[str] = None
    sanitized_query: Optional[str] = None
    pii_detected: List[Dict[str, Any]] = []
    confidence: float = 1.0

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "guardrails-service"}

@app.post("/check/input", response_model=GuardrailsResponse)
async def check_input(request: GuardrailsRequest):
    """Check user input for PII, topical relevance, and blocked content."""
    # PII detection
    pii_result = pii_guard.detect(request.query)
    if pii_result["has_pii"]:
        sanitized = pii_guard.anonymize(request.query)
        return GuardrailsResponse(
            passed=False,
            layer="pii",
            reason="PII detected in input",
            sanitized_query=sanitized,
            pii_detected=pii_result["entities"]
        )

    # Topical check
    topical = topical_guard.check(request.query)
    if not topical["allowed"]:
        return GuardrailsResponse(
            passed=False,
            layer="topical",
            reason=topical["reason"]
        )

    # Execution guard
    exec_check = execution_guard.check(request.query)
    if not exec_check["allowed"]:
        return GuardrailsResponse(
            passed=False,
            layer="execution",
            reason=exec_check["reason"]
        )

    return GuardrailsResponse(passed=True, layer="all", confidence=topical.get("confidence", 1.0))

@app.post("/check/output", response_model=GuardrailsResponse)
async def check_output(request: GuardrailsRequest):
    """Check AI output for hallucinations and PII leakage."""
    if not request.response:
        raise HTTPException(400, "Response required for output check")

    # Hallucination check for tax/legal queries
    if request.intent in ["tax_advisory", "fema_advisory", "transfer_pricing"]:
        hall_result = hallucination_guard.check(request.response, request.context or [])
        if not hall_result["grounded"]:
            return GuardrailsResponse(
                passed=False,
                layer="hallucination",
                reason=hall_result["reason"],
                confidence=hall_result.get("confidence", 0.0)
            )

    # PII leakage check
    pii_result = pii_guard.detect(request.response)
    if pii_result["has_pii"]:
        return GuardrailsResponse(
            passed=False,
            layer="pii_leak",
            reason="PII detected in AI response",
            pii_detected=pii_result["entities"]
        )

    return GuardrailsResponse(passed=True, layer="all", confidence=1.0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
