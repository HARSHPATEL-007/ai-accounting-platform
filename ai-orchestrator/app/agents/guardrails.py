from app.models.state import AgentState, ConfidenceLevel
from app.core.logging import logger
from typing import Dict, Any
import re

class GuardrailsChecker:
    """Multi-layer guardrails for hallucination prevention, topical filtering, and execution safety."""

    def __init__(self, guardrails_service_url: str = "http://guardrails-service:8000"):
        self.guardrails_url = guardrails_service_url
        self.topical_keywords = [
            'accounting', 'tax', 'gst', 'income tax', 'fema', 'dtaa', 'esop', '409a',
            'valuation', 'audit', 'ledger', 'invoice', 'cma', 'bank', 'financial',
            'compliance', 'section', 'transfer pricing', 'mca', 'cbic', 'tds'
        ]
        self.blocked_patterns = [
            r'\b(bitcoin|crypto trading|stock tip|investment advice|buy this stock)\b',
            r'\b(hack|exploit|bypass|illegal)\b',
        ]

    async def check_topical(self, state: AgentState) -> Dict[str, Any]:
        query_lower = state.query.lower()
        is_topical = any(kw in query_lower for kw in self.topical_keywords)
        for pattern in self.blocked_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"passed": False, "layer": "topical", "reason": "Query contains blocked content"}
        if not is_topical:
            return {"passed": False, "layer": "topical", "reason": "Query is not related to accounting/taxation/compliance"}
        return {"passed": True, "layer": "topical"}

    async def check_hallucination(self, state: AgentState) -> Dict[str, Any]:
        if not state.citations:
            if state.intent in ['tax_advisory', 'fema_advisory', 'transfer_pricing']:
                return {"passed": False, "layer": "hallucination", "reason": "Tax/legal query without citations"}
            return {"passed": True, "layer": "hallucination"}
        for citation in state.citations:
            if not citation.get('source_url') or not citation.get('document_title'):
                return {"passed": False, "layer": "hallucination", "reason": "Invalid citation format"}
        return {"passed": True, "layer": "hallucination"}

    async def check_execution(self, state: AgentState) -> Dict[str, Any]:
        blocked_actions = ['file tax return', 'submit gst', 'execute transfer', 'modify ledger', 'send email']
        query_lower = state.query.lower()
        for action in blocked_actions:
            if action in query_lower:
                return {"passed": False, "layer": "execution", "reason": f"Autonomous action '{action}' requires human approval"}
        return {"passed": True, "layer": "execution"}

    async def run_all_checks(self, state: AgentState) -> AgentState:
        trace_id = state.execution_trace_id
        logger.info("guardrails_check_start", trace_id=trace_id)
        checks = [await self.check_topical(state), await self.check_hallucination(state), await self.check_execution(state)]
        for check in checks:
            if not check["passed"]:
                state.requires_human_review = True
                state.human_review_reason = check["reason"]
                state.confidence_level = ConfidenceLevel.LOW
                state.draft_response = f"[GUARDRAIL TRIGGERED - {check['layer'].upper()}] {check['reason']}. Requires human CPA verification."
                logger.warning("guardrails_blocked", trace_id=trace_id, layer=check['layer'], reason=check['reason'])
                return state
        logger.info("guardrails_passed", trace_id=trace_id)
        return state
