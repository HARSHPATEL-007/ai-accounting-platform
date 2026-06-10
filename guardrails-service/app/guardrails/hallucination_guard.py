from typing import Dict, Any, List
import re

class HallucinationGuard:
    """Verify AI responses are grounded in retrieved context."""

    def check(self, response: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not context:
            # If no context and response makes specific claims, flag it
            if self._has_specific_claims(response):
                return {
                    "grounded": False,
                    "reason": "Response contains specific claims but no source context was retrieved",
                    "confidence": 0.2
                }
            return {"grounded": True, "reason": "No context needed for general response", "confidence": 0.8}

        # Check if cited sections appear in context
        cited_sections = self._extract_citations(response)
        context_sections = [c.get("metadata", {}).get("section", "").lower() for c in context]

        for cited in cited_sections:
            if cited and cited.lower() not in context_sections:
                return {
                    "grounded": False,
                    "reason": f"Cited section '{cited}' not found in retrieved context",
                    "confidence": 0.3
                }

        # Check if response contains specific numbers not in context
        response_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', response))
        context_text = " ".join([c.get("content", "") for c in context])
        context_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', context_text))

        ungrounded_numbers = response_numbers - context_numbers
        if len(ungrounded_numbers) > 3:
            return {
                "grounded": False,
                "reason": f"Response contains {len(ungrounded_numbers)} numerical values not present in source context",
                "confidence": 0.4
            }

        return {"grounded": True, "reason": "Response is grounded in retrieved context", "confidence": 0.9}

    def _has_specific_claims(self, text: str) -> bool:
        patterns = [
            r'Section\s+\d+[A-Z]*',
            r'\d{1,2}%\s+tax',
            r'Rs\.\s*\d+',
            r'INR\s*\d+',
            r'penalty of\s+\d+'
        ]
        return any(re.search(p, text) for p in patterns)

    def _extract_citations(self, text: str) -> List[str]:
        pattern = r'Section\s+(\d+[A-Z]*)'
        return list(set(re.findall(pattern, text, re.IGNORECASE)))
