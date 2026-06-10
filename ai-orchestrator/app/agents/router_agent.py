from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.state import RouterOutput, IntentType
from app.core.logging import logger
from typing import Dict, Any

ROUTER_PROMPT = """You are the Router Agent for an AI-Native Indian Accounting Platform.
Analyze the user query and classify it into exactly one intent.

Available intents:
- generate_cma: Generate CMA (Credit Monitoring Arrangement) data for bank loans
- fema_advisory: Questions about FEMA (Foreign Exchange Management Act) compliance
- esop_valuation: ESOP or 409A valuation requests
- gst_reconciliation: GST return reconciliation, GSTR-1/GSTR-3B issues
- audit_query: Internal/statutory audit questions, anomaly detection
- tax_advisory: Income tax, DTAA, transfer pricing, Section 115BAC, etc.
- document_analysis: Analyze contracts, ESG reports, M&A documents
- transfer_pricing: TP documentation, CUP/TNMM methods
- general_chat: General accounting/financial questions
- unknown: Cannot determine intent

Rules:
1. If the query mentions tax sections, rates, or tax compliance -> tax_advisory
2. If about foreign investment, subsidiary setup, FEMA -> fema_advisory
3. If about employee stock options, vesting, valuation -> esop_valuation
4. If about bank loan data, CMA reports -> generate_cma
5. If about GST returns, invoices, HSN codes -> gst_reconciliation
6. Confidence must be >= 0.85 for direct routing, else flag for human review

Query: {query}

Respond with JSON matching the RouterOutput schema."""

class RouterAgent:
    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.0)
        self.prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
        self.chain = self.prompt | self.llm.with_structured_output(RouterOutput)

    async def route(self, query: str, client_id: str, trace_id: str) -> Dict[str, Any]:
        logger.info("routing_query", trace_id=trace_id, client_id=client_id, query=query[:100])
        try:
            result: RouterOutput = await self.chain.ainvoke({"query": query})
            requires_human = result.confidence < 0.85
            logger.info("routing_complete", trace_id=trace_id, intent=result.intent, confidence=result.confidence, requires_human=requires_human)
            return {
                "intent": result.intent,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "target_agent": result.target_agent,
                "requires_human_review": requires_human,
                "trace_id": trace_id
            }
        except Exception as e:
            logger.error("routing_failed", trace_id=trace_id, error=str(e))
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "reasoning": f"Routing failed: {str(e)}",
                "target_agent": "human_fallback",
                "requires_human_review": True,
                "trace_id": trace_id
            }
