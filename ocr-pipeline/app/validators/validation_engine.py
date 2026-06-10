from typing import Dict, Any, List
import re
from app.core.logging import logger

class ValidationEngine:
    """Validate extracted data against business rules."""

    GSTIN_REGEX = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    HSN_REGEX = r'^[0-9]{4,8}$'

    def validate_gstin(self, gstin: str) -> Dict[str, Any]:
        """Validate GSTIN format and check digit."""
        if not re.match(self.GSTIN_REGEX, gstin):
            return {"valid": False, "error": "Invalid GSTIN format"}

        # Check state code (first 2 digits)
        state_code = int(gstin[:2])
        if state_code < 1 or state_code > 37:
            return {"valid": False, "error": f"Invalid state code: {state_code}"}

        return {"valid": True, "state_code": state_code, "pan": gstin[2:12]}

    def validate_hsn(self, hsn: str) -> Dict[str, Any]:
        """Validate HSN code."""
        if not re.match(self.HSN_REGEX, hsn):
            return {"valid": False, "error": "HSN must be 4-8 digits"}
        return {"valid": True, "length": len(hsn)}

    def validate_document(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Run full validation suite on extracted document data."""
        errors = []
        warnings = []

        # Validate GSTINs
        for gstin in extracted.get("gstin", []):
            result = self.validate_gstin(gstin)
            if not result["valid"]:
                errors.append(f"Invalid GSTIN: {gstin} - {result['error']}")

        # Validate HSN codes
        for hsn in extracted.get("hsn_codes", []):
            result = self.validate_hsn(hsn)
            if not result["valid"]:
                warnings.append(f"Invalid HSN: {hsn}")

        # Check for duplicates (simplified)
        if not extracted.get("amounts"):
            warnings.append("No amounts detected")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "can_auto_post": len(errors) == 0 and len(warnings) <= 2
        }

    def detect_duplicates(self, new_doc: Dict[str, Any], existing_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential duplicate invoices using fuzzy matching."""
        duplicates = []
        new_gstin = set(new_doc.get("gstin", []))
        new_inv = new_doc.get("invoice_number")

        for doc in existing_docs:
            score = 0
            if new_inv and doc.get("invoice_number") == new_inv:
                score += 0.5
            if new_gstin.intersection(set(doc.get("gstin", []))):
                score += 0.3
            if score > 0.6:
                duplicates.append({"doc_id": doc.get("id"), "confidence": score})

        return duplicates
