from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.models.state import AgentState, IntentType
from app.agents.router_agent import RouterAgent
from app.agents.tax_agent import TaxComplianceAgent
from app.agents.quantitative_agent import QuantitativeAgent
from app.agents.guardrails import GuardrailsChecker
from app.core.logging import logger
from typing import Dict, Any
import uuid

class AccountingWorkflow:
    """LangGraph-based multi-agent workflow for the accounting platform."""

    def __init__(self):
        self.router = RouterAgent()
        self.tax_agent = TaxComplianceAgent()
        self.quant_agent = QuantitativeAgent()
        self.guardrails = GuardrailsChecker()
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("guardrails_input", self._input_guardrails)
        workflow.add_node("router", self._route)
        workflow.add_node("tax_agent", self._run_tax_agent)
        workflow.add_node("quant_agent", self._run_quant_agent)
        workflow.add_node("human_fallback", self._human_fallback)
        workflow.add_node("guardrails_output", self._output_guardrails)
        workflow.add_node("finalize", self._finalize)

        workflow.set_entry_point("guardrails_input")
        workflow.add_conditional_edges("guardrails_input", self._check_input_guardrails, {"passed": "router", "blocked": "human_fallback"})
        workflow.add_conditional_edges("router", self._route_decision, {"tax": "tax_agent", "quant": "quant_agent", "human": "human_fallback", "unknown": "human_fallback"})
        workflow.add_edge("tax_agent", "guardrails_output")
        workflow.add_edge("quant_agent", "guardrails_output")
        workflow.add_edge("human_fallback", "finalize")
        workflow.add_conditional_edges("guardrails_output", self._check_output_guardrails, {"passed": "finalize", "blocked": "human_fallback"})
        workflow.add_edge("finalize", END)
        return workflow.compile(checkpointer=self.memory)

    async def _input_guardrails(self, state: AgentState) -> AgentState:
        state.execution_trace_id = str(uuid.uuid4())
        logger.info("workflow_start", trace_id=state.execution_trace_id, client_id=state.client_id)
        return state

    def _check_input_guardrails(self, state: AgentState) -> str:
        return "passed"

    async def _route(self, state: AgentState) -> AgentState:
        result = await self.router.route(state.query, state.client_id or "unknown", state.execution_trace_id)
        state.intent = result["intent"]
        state.intent_confidence = result["confidence"]
        state.requires_human_review = result["requires_human_review"]
        return state

    def _route_decision(self, state: AgentState) -> str:
        if state.requires_human_review:
            return "human"
        mapping = {
            IntentType.TAX_ADVISORY: "tax", IntentType.FEMA_ADVISORY: "tax",
            IntentType.GST_RECONCILIATION: "tax", IntentType.AUDIT_QUERY: "tax",
            IntentType.ESOP_VALUATION: "quant", IntentType.GENERATE_CMA: "quant",
            IntentType.TRANSFER_PRICING: "quant", IntentType.DOCUMENT_ANALYSIS: "tax",
            IntentType.GENERAL_CHAT: "tax", IntentType.UNKNOWN: "unknown"
        }
        return mapping.get(state.intent, "human")

    async def _run_tax_agent(self, state: AgentState) -> AgentState:
        return await self.tax_agent.process(state)

    async def _run_quant_agent(self, state: AgentState) -> AgentState:
        return await self.quant_agent.process(state)

    async def _human_fallback(self, state: AgentState) -> AgentState:
        state.final_response = (
            f"Your query requires review by a licensed Chartered Accountant.\n\n"
            f"Reason: {state.human_review_reason or 'Complex or sensitive accounting matter'}\n\n"
            f"A CA will respond within 24 hours."
        )
        state.confidence_level = "low"
        logger.info("human_fallback_triggered", trace_id=state.execution_trace_id, reason=state.human_review_reason)
        return state

    async def _output_guardrails(self, state: AgentState) -> AgentState:
        return await self.guardrails.run_all_checks(state)

    def _check_output_guardrails(self, state: AgentState) -> str:
        return "passed" if not state.requires_human_review else "blocked"

    async def _finalize(self, state: AgentState) -> AgentState:
        if not state.final_response:
            state.final_response = state.draft_response
        disclaimer = (
            "\n\n---\n\n**Disclaimer:** This AI-generated response is for informational purposes only "
            "and does not constitute professional financial or legal advice. Please consult a licensed "
            "Chartered Accountant before making decisions."
        )
        if disclaimer not in state.final_response:
            state.final_response += disclaimer
        logger.info("workflow_complete", trace_id=state.execution_trace_id, confidence=state.confidence_level)
        return state

    async def invoke(self, query: str, client_id: str, user_id: str) -> Dict[str, Any]:
        initial_state = AgentState(query=query, client_id=client_id, user_id=user_id)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await self.graph.ainvoke(initial_state.dict(), config)
        return {
            "response": result.get("final_response"),
            "confidence": result.get("confidence_level"),
            "citations": result.get("citations", []),
            "intent": result.get("intent"),
            "requires_human_review": result.get("requires_human_review"),
            "trace_id": result.get("execution_trace_id"),
            "tools_called": result.get("tools_called", [])
        }
