import numpy as np
from typing import List, Dict, Any, Optional
import httpx
from sentence_transformers import SentenceTransformer, CrossEncoder
from elasticsearch import Elasticsearch
from app.core.config import settings
from app.core.logging import logger
import time

class HybridRetriever:
    """Hybrid search combining dense (Pinecone) and sparse (BM25/Elasticsearch) retrieval."""

    def __init__(self):
        self.dense_model = SentenceTransformer(settings.embedding_model)
        self.reranker = CrossEncoder(settings.rerank_model)
        self.es = Elasticsearch([settings.elasticsearch_url])
        self.alpha = settings.hybrid_alpha

    def _encode_query(self, query: str) -> List[float]:
        return self.dense_model.encode(query).tolist()

    def _dense_search(self, query_vector: List[float], top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search Pinecone dense index."""
        try:
            import pinecone
            pc = pinecone.Pinecone(api_key=settings.pinecone_api_key)
            index = pc.Index(settings.pinecone_index)

            result = index.query(
                vector=query_vector,
                top_k=top_k * 2,  # Over-fetch for re-ranking
                namespace=settings.pinecone_namespace,
                filter=filters,
                include_metadata=True
            )

            docs = []
            for match in result.matches:
                docs.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "source": "dense"
                })
            return docs
        except Exception as e:
            logger.error("dense_search_failed", error=str(e))
            return []

    def _sparse_search(self, query: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search Elasticsearch BM25 index."""
        try:
            es_query = {
                "bool": {
                    "must": {"multi_match": {"query": query, "fields": ["content^2", "title", "metadata.section"]}},
                    "filter": [{"term": {k: v}} for k, v in filters.items()]
                }
            }

            result = self.es.search(index="rag_documents", body={
                "query": es_query,
                "size": top_k * 2,
                "_source": ["id", "title", "content", "source_url", "doc_type", "jurisdiction", "metadata", "chunk_index"]
            })

            docs = []
            for hit in result["hits"]["hits"]:
                docs.append({
                    "id": hit["_id"],
                    "score": hit["_score"] / 100.0,  # Normalize BM25 score roughly
                    "metadata": hit["_source"],
                    "source": "sparse"
                })
            return docs
        except Exception as e:
            logger.error("sparse_search_failed", error=str(e))
            return []

    def _fuse_scores(self, dense_results: List[Dict], sparse_results: List[Dict], alpha: float) -> List[Dict]:
        """Fuse dense and sparse scores using weighted combination."""
        scores = {}

        for doc in dense_results:
            doc_id = doc["id"]
            scores[doc_id] = {
                "dense": doc["score"],
                "sparse": 0.0,
                "metadata": doc["metadata"],
                "sources": ["dense"]
            }

        for doc in sparse_results:
            doc_id = doc["id"]
            if doc_id in scores:
                scores[doc_id]["sparse"] = doc["score"]
                scores[doc_id]["sources"].append("sparse")
            else:
                scores[doc_id] = {
                    "dense": 0.0,
                    "sparse": doc["score"],
                    "metadata": doc["metadata"],
                    "sources": ["sparse"]
                }

        # Normalize and combine
        max_dense = max([s["dense"] for s in scores.values()]) if scores else 1.0
        max_sparse = max([s["sparse"] for s in scores.values()]) if scores else 1.0

        fused = []
        for doc_id, score_data in scores.items():
            norm_dense = score_data["dense"] / max_dense if max_dense > 0 else 0
            norm_sparse = score_data["sparse"] / max_sparse if max_sparse > 0 else 0
            hybrid = alpha * norm_dense + (1 - alpha) * norm_sparse

            fused.append({
                "id": doc_id,
                "hybrid_score": hybrid,
                "dense_score": norm_dense,
                "sparse_score": norm_sparse,
                "metadata": score_data["metadata"],
                "sources": score_data["sources"]
            })

        fused.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return fused

    def _rerank(self, query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
        """Re-rank top candidates using cross-encoder."""
        if not candidates:
            return []

        pairs = [(query, c["metadata"].get("content", "")[:512]) for c in candidates[:top_k * 2]]
        scores = self.reranker.predict(pairs)

        for i, score in enumerate(scores):
            if i < len(candidates):
                candidates[i]["rerank_score"] = float(score)

        candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return candidates[:top_k]

    async def retrieve(self, query: str, jurisdiction: str = "central", 
                      doc_type: Optional[str] = None, top_k: int = 5,
                      alpha: Optional[float] = None) -> Dict[str, Any]:
        start = time.time()
        alpha = alpha or self.alpha

        filters = {"jurisdiction": jurisdiction}
        if doc_type:
            filters["doc_type"] = doc_type

        logger.info("retrieval_start", query=query[:100], jurisdiction=jurisdiction, alpha=alpha)

        # Parallel dense + sparse search
        query_vector = self._encode_query(query)
        dense_results = self._dense_search(query_vector, top_k, filters)
        sparse_results = self._sparse_search(query, top_k, filters)

        # Fuse and re-rank
        fused = self._fuse_scores(dense_results, sparse_results, alpha)
        reranked = self._rerank(query, fused, top_k)

        elapsed = (time.time() - start) * 1000

        logger.info("retrieval_complete", query=query[:100], results=len(reranked), time_ms=elapsed)

        return {
            "query": query,
            "results": reranked,
            "total_found": len(fused),
            "retrieval_time_ms": round(elapsed, 2),
            "strategy": "hybrid_dense_sparse_rerank"
        }
