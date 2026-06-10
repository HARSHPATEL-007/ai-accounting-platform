from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import RetrieveRequest, RetrieveResponse, IngestRequest, IngestResponse
from app.retrieval.hybrid_search import HybridRetriever
from app.core.config import settings
from app.core.logging import logger
import time

app = FastAPI(
    title="RAG Service - Hybrid Search",
    description="Dense + Sparse hybrid retrieval for Indian tax/legal documents",
    version="1.0.0"
)

retriever = HybridRetriever()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "rag-service", "index": settings.pinecone_index}

@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: RetrieveRequest):
    try:
        result = await retriever.retrieve(
            query=request.query,
            jurisdiction=request.jurisdiction,
            doc_type=request.doc_type,
            top_k=request.top_k,
            alpha=request.alpha
        )

        # Map to response schema
        docs = []
        for r in result["results"]:
            meta = r["metadata"]
            docs.append({
                "id": r["id"],
                "title": meta.get("title", "Unknown"),
                "content": meta.get("content", "")[:1000],
                "source_url": meta.get("source_url", ""),
                "doc_type": meta.get("doc_type", "unknown"),
                "jurisdiction": meta.get("jurisdiction", "central"),
                "section": meta.get("metadata", {}).get("section"),
                "metadata": meta.get("metadata", {}),
                "dense_score": r["dense_score"],
                "sparse_score": r["sparse_score"],
                "hybrid_score": r["hybrid_score"],
                "rerank_score": r.get("rerank_score")
            })

        return RetrieveResponse(
            query=result["query"],
            results=docs,
            total_found=result["total_found"],
            retrieval_time_ms=result["retrieval_time_ms"],
            strategy=result["strategy"]
        )
    except Exception as e:
        logger.error("retrieval_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """Ingest a new document into the RAG pipeline."""
    # In production: chunk, embed, upsert to Pinecone + Elasticsearch
    logger.info("ingest_request", url=request.source_url, title=request.title)
    return IngestResponse(status="accepted", chunks_ingested=0, document_id="pending")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
