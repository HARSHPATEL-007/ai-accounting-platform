from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import time

from app.agents.workflow import AccountingWorkflow
from app.core.config import settings
from app.core.logging import logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

REQUEST_COUNT = Counter('ai_orchestrator_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('ai_orchestrator_request_duration_seconds', 'Request latency', ['endpoint'])
AGENT_ROUTING = Counter('agent_routing_total', 'Agent routing decisions', ['intent', 'target'])

app = FastAPI(
    title="AI Orchestrator - Accounting Platform",
    description="Multi-agent AI orchestration for Indian accounting, tax, and compliance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://accounting-platform.in", "https://app.accounting-platform.in"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)
workflow = AccountingWorkflow()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=5000, description="User query")
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID")

class QueryResponse(BaseModel):
    response: str
    confidence: str
    citations: List[Dict[str, Any]]
    intent: str
    requires_human_review: bool
    trace_id: str
    tools_called: List[str]
    processing_time_ms: float

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-orchestrator", "version": "1.0.0"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    logger.info("query_received", trace_id=trace_id, client_id=request.client_id, user_id=request.user_id, query_length=len(request.query))
    try:
        result = await workflow.invoke(query=request.query, client_id=request.client_id, user_id=request.user_id)
        processing_time = (time.time() - start_time) * 1000
        AGENT_ROUTING.labels(intent=result.get("intent", "unknown"), target="human" if result.get("requires_human_review") else "ai").inc()
        logger.info("query_completed", trace_id=trace_id, intent=result.get("intent"), confidence=result.get("confidence"), human_review=result.get("requires_human_review"), processing_time_ms=processing_time)
        return QueryResponse(
            response=result["response"], confidence=result["confidence"], citations=result.get("citations", []),
            intent=result["intent"], requires_human_review=result["requires_human_review"], trace_id=result["trace_id"],
            tools_called=result.get("tools_called", []), processing_time_ms=round(processing_time, 2)
        )
    except Exception as e:
        logger.error("query_failed", trace_id=trace_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@app.post("/batch")
async def batch_process(requests: List[QueryRequest], background_tasks: BackgroundTasks):
    results = []
    for req in requests:
        result = await process_query(req)
        results.append(result)
    return {"results": results, "batch_size": len(results)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
