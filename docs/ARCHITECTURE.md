# Architecture Decision Records

## ADR-001: Multi-Agent Architecture with LangGraph

**Status**: Accepted
**Date**: 2024-06-01

### Context
Accounting requires zero hallucinations. We need a system where deterministic math engines handle calculations, and LLMs handle reasoning and unstructured data.

### Decision
Implement a Multi-Agent Architecture using LangGraph with the following agents:
- Router Agent: Intent classification with confidence threshold (0.85)
- Tax & Compliance Agent: Connected to legal RAG pipeline
- Quantitative Agent: Delegates to deterministic math engine
- Document Analysis Agent: OCR + LLM extraction
- Foreign Entity Agent: Cross-border tax structuring

### Consequences
- Positive: Modular, testable, extensible
- Negative: Increased latency due to multi-hop reasoning
- Mitigation: Async processing, caching, HPA scaling

## ADR-002: Hybrid Search RAG (Dense + Sparse)

**Status**: Accepted
**Date**: 2024-06-01

### Context
Indian tax code requires exact section number retrieval. Pure vector search may miss specific statutory references.

### Decision
Implement Hybrid Search combining:
- Dense: Pinecone/Milvus with sentence-transformers embeddings
- Sparse: Elasticsearch BM25 for keyword matching
- Score: `Score(q,d) = 0.7 * CosineSim + 0.3 * BM25`
- Re-ranking: Cross-encoder (ms-marco-MiniLM-L-6-v2)

### Consequences
- Positive: High recall for exact section numbers
- Negative: Dual index maintenance, higher compute
- Mitigation: Batch embedding, managed Elasticsearch

## ADR-003: Go for Ledger Processing

**Status**: Accepted
**Date**: 2024-06-01

### Context
Financial ledgers require ACID compliance, high throughput, and low latency.

### Decision
Use Go (Gin/Echo) with PostgreSQL for ledger processing:
- pgxpool for connection pooling
- COPY FROM for bulk inserts
- Partitioned tables by client_id + date
- Immutable hash chain for tamper detection

### Consequences
- Positive: High performance, type safety, efficient concurrency
- Negative: Smaller ecosystem than Python for AI/ML
- Mitigation: Keep AI/ML in Python microservices

## ADR-004: Temporal for Workflow Orchestration

**Status**: Accepted
**Date**: 2024-06-01

### Context
Invoice-to-Ledger STP requires reliable orchestration with compensation on failure.

### Decision
Use Temporal.io for:
- Straight-Through Processing workflows
- Saga pattern for compensation
- Idempotency keys
- Retry policies with exponential backoff

### Consequences
- Positive: Durable execution, replay capability, observability
- Negative: Operational complexity of Temporal cluster
- Mitigation: Managed Temporal Cloud or auto-setup container

## ADR-005: Three-Layer AI Guardrails

**Status**: Accepted
**Date**: 2024-06-01

### Context
Financial data is highly sensitive. AI must not hallucinate tax rates or autonomously execute transactions.

### Decision
Implement three guardrail layers:
1. Topical: Regex + classifier blocking non-accounting queries
2. Hallucination: Self-reflection loop verifying citations against retrieved context
3. Execution: Block autonomous filing, transfers, ledger modifications

### Consequences
- Positive: Reduced risk, SOC 2 compliance
- Negative: Some legitimate queries may be blocked
- Mitigation: Human-in-the-loop fallback, confidence scoring
