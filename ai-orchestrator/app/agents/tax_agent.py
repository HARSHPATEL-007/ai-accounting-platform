from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.state import AgentState, Citation, ConfidenceLevel
from app.core.logging import logger
from typing import List, Dict, Any
import httpx

TAX_PROMPT = """You are the Tax & Compliance Agent for an Indian Accounting Platform.
You have access to the following legal context retrieved from official sources.

CRITICAL RULES:
1. You MUST cite exact section numbers (e.g., Section 115BAC, Section 12(1)) and document names
2. You MUST NOT hallucinate tax rates, section numbers, or legal provisions
3. If the retrieved context does not contain the answer, respond: "Requires human CPA verification."
4. Always include the mandatory disclaimer at the end

Retrieved Context:
{context}

User Query: {query}

Respond in this format:
ANSWER: [Your detailed answer with citations]
CITATIONS: [List of sources with section numbers]
CONFIDENCE: [high/medium/low based on context coverage]

Mandatory Disclaimer: This AI-generated response is for informational purposes only and does not constitute professional financial or legal advice. Please consult a licensed Chartered Accountant before making decisions."""

class TaxComplianceAgent:
    def __init__(self, llm_model: str = "gpt-4o", rag_service_url: str = "http://rag-service:8000"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(TAX_PROMPT)
        self.chain = self.prompt | self.llm
        self.rag_url = rag_service_url

    async def retrieve_context(self, query: str, jurisdiction: str = "central") -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.rag_url}/retrieve",
                    json={"query": query, "jurisdiction": jurisdiction, "top_k": 5},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("results", [])
            except Exception as e:
                logger.error("rag_retrieval_failed", error=str(e))
                return []

    async def process(self, state: AgentState) -> AgentState:
        trace_id = state.execution_trace_id
        logger.info("tax_agent_processing", trace_id=trace_id, query=state.query[:100])

        context_results = await self.retrieve_context(state.query)
        state.retrieved_context = context_results

        context_text = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\nSection: {r.get('metadata', {}).get('section', 'N/A')}\n{r.get('content', '')}"
            for r in context_results
        ]) if context_results else "NO RELEVANT CONTEXT FOUND."

        response = await self.chain.ainvoke({"context": context_text, "query": state.query})
        content = response.content if hasattr(response, "content") else str(response)

        confidence = ConfidenceLevel.LOW
        if "CONFIDENCE: high" in content:
            confidence = ConfidenceLevel.HIGH
        elif "CONFIDENCE: medium" in content:
            confidence = ConfidenceLevel.MEDIUM

        citations = []
        for r in context_results:
            citations.append(Citation(
                source_url=r.get("source_url", ""),
                document_title=r.get("title", ""),
                section=r.get("metadata", {}).get("section"),
                excerpt=r.get("content", "")[:200]
            ).dict())

        state.citations = citations
        state.confidence_level = confidence
        state.draft_response = content
        state.tools_called.append("search_tax_code")

        if not context_results and "Requires human CPA verification" not in content:
            state.requires_human_review = True
            state.human_review_reason = "No legal context retrieved and response lacks CPA verification disclaimer"
            state.draft_response = "Requires human CPA verification. Insufficient legal context retrieved for this query."

        logger.info("tax_agent_complete", trace_id=trace_id, confidence=confidence, citations=len(citations))
        return state
