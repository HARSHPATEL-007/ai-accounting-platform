from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Dict, Any, List

class PIIGuard:
    """Detect and anonymize PII before sending to LLMs."""

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.sensitive_entities = [
            "IN_PAN", "IN_AADHAAR", "CREDIT_CARD", "IBAN", "US_BANK_NUMBER",
            "EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "LOCATION"
        ]

    def detect(self, text: str) -> Dict[str, Any]:
        results = self.analyzer.analyze(text=text, language="en", entities=self.sensitive_entities)
        entities = []
        for r in results:
            entities.append({
                "type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score,
                "text": text[r.start:r.end]
            })
        return {"has_pii": len(entities) > 0, "entities": entities, "count": len(entities)}

    def anonymize(self, text: str) -> str:
        results = self.analyzer.analyze(text=text, language="en", entities=self.sensitive_entities)
        operators = {e.entity_type: OperatorConfig("replace", {"new_value": f"<{e.entity_type}>"}) for e in results}
        return self.anonymizer.anonymize(text=text, analyzer_results=results, operators=operators).text
