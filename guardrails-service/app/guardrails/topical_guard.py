import re
from typing import Dict, Any

class TopicalGuard:
    """Ensure queries are accounting/tax/compliance related."""

    ALLOWED_TOPICS = [
        'accounting', 'tax', 'gst', 'income tax', 'fema', 'dtaa', 'esop', '409a',
        'valuation', 'audit', 'ledger', 'invoice', 'cma', 'bank', 'financial',
        'compliance', 'section', 'transfer pricing', 'mca', 'cbic', 'tds', 'tds return',
        'advance tax', 'depreciation', 'capital gains', 'dividend', 'salary',
        'business income', 'professional tax', 'roc filing', 'moa', 'aoa',
        'board resolution', 'share capital', 'private limited', 'llp', 'partnership'
    ]

    BLOCKED_PATTERNS = [
        r'\b(bitcoin|ethereum|crypto trading|nft|blockchain investment)\b',
        r'\b(stock tip|buy this stock|investment advice|market prediction)\b',
        r'\b(hack|exploit|bypass|illegal|evade tax|tax evasion)\b',
        r'\b(porn|adult|gambling|casino|betting)\b',
        r'\b(bomb|terrorist|weapon|kill|murder)\b',
    ]

    def check(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()

        # Check blocked patterns first
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"allowed": False, "reason": "Query contains prohibited content", "confidence": 0.0}

        # Check topical relevance
        is_topical = any(topic in query_lower for topic in self.ALLOWED_TOPICS)

        if not is_topical:
            return {
                "allowed": False,
                "reason": "I can only assist with accounting, taxation, compliance, and financial advisory matters.",
                "confidence": 0.0
            }

        return {"allowed": True, "reason": "Topical check passed", "confidence": 1.0}
