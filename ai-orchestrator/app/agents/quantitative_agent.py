from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.models.state import AgentState, ConfidenceLevel
from app.core.logging import logger
from typing import Dict, Any
import httpx

QUANT_PROMPT = """You are the Quantitative Agent for an Indian Accounting Platform.
You handle ESOP valuations, 409A valuations, transfer pricing calculations, and CMA data generation.

CRITICAL RULES:
1. All mathematical calculations MUST be performed by the deterministic math engine, not by you
2. You structure inputs and interpret outputs only
3. For ESOP: Use Black-Scholes model inputs (S, K, T, r, sigma)
4. For Transfer Pricing: Reference CUP, TNMM, or RPM methods based on data
5. For CMA: Generate structured financial data in prescribed bank format

Math Engine Results:
{calculation_results}

User Query: {query}

Provide a structured response with:
1. Methodology used
2. Key assumptions
3. Results summary
4. Confidence level (high/medium/low)

Mandatory Disclaimer: This AI-generated response is for informational purposes only and does not constitute professional financial or legal advice. Please consult a licensed Chartered Accountant before making decisions."""

class QuantitativeAgent:
    def __init__(self, llm_model: str = "gpt-4o", valuation_url: str = "http://valuation-engine:8000"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(QUANT_PROMPT)
        self.chain = self.prompt | self.llm
        self.valuation_url = valuation_url

    async def call_math_engine(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.valuation_url}/calculate",
                    json={"tool": tool, "parameters": params},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("math_engine_failed", tool=tool, error=str(e))
                return {"error": str(e), "result": None}

    async def process(self, state: AgentState) -> AgentState:
        trace_id = state.execution_trace_id
        logger.info("quant_agent_processing", trace_id=trace_id, query=state.query[:100])

        calc_type = "black_scholes" if "esop" in state.query.lower() or "409a" in state.query.lower() else "generic"
        calc_result = await self.call_math_engine(calc_type, {"query": state.query})
        state.calculation_results = calc_result

        response = await self.chain.ainvoke({"calculation_results": str(calc_result), "query": state.query})
        content = response.content if hasattr(response, "content") else str(response)

        state.draft_response = content
        state.confidence_level = ConfidenceLevel.HIGH if not calc_result.get("error") else ConfidenceLevel.LOW
        state.tools_called.append("python_repl")
        state.tools_called.append("calculator_api")

        if calc_result.get("error"):
            state.requires_human_review = True
            state.human_review_reason = f"Math engine error: {calc_result['error']}"

        logger.info("quant_agent_complete", trace_id=trace_id, calc_error=calc_result.get("error"))
        return state
