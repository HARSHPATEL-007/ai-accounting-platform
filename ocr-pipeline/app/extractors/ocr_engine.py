import pytesseract
from PIL import Image
import pdf2image
from typing import Dict, Any, List
import io
import re
from app.core.config import settings
from app.core.logging import logger

class OCREngine:
    """Extract text and structured data from documents using Tesseract + LLM."""

    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_from_image(self, image: Image.Image) -> Dict[str, Any]:
        """Run OCR on an image."""
        try:
            text = pytesseract.image_to_string(image, lang="eng")
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Calculate confidence
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0

            return {
                "raw_text": text,
                "confidence": round(avg_conf / 100.0, 4),
                "word_count": len(text.split()),
                "language": "eng"
            }
        except Exception as e:
            logger.error("ocr_extraction_failed", error=str(e))
            return {"raw_text": "", "confidence": 0.0, "error": str(e)}

    def extract_from_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Convert PDF to images and OCR each page."""
        try:
            images = pdf2image.convert_from_bytes(pdf_bytes, dpi=300)
            results = []
            for i, img in enumerate(images):
                page_result = self.extract_from_image(img)
                page_result["page_number"] = i + 1
                results.append(page_result)
            return results
        except Exception as e:
            logger.error("pdf_conversion_failed", error=str(e))
            return [{"page_number": 1, "raw_text": "", "confidence": 0.0, "error": str(e)}]

    def extract_structured(self, raw_text: str) -> Dict[str, Any]:
        """Extract structured fields using regex patterns (fallback before LLM)."""
        structured = {
            "gstin": self._extract_gstin(raw_text),
            "hsn_codes": self._extract_hsn(raw_text),
            "dates": self._extract_dates(raw_text),
            "amounts": self._extract_amounts(raw_text),
            "invoice_number": self._extract_invoice_number(raw_text),
            "vendor_name": None,
            "line_items": []
        }
        return structured

    def _extract_gstin(self, text: str) -> List[str]:
        pattern = r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b'
        return list(set(re.findall(pattern, text)))

    def _extract_hsn(self, text: str) -> List[str]:
        pattern = r'\b[0-9]{4,8}\b'
        candidates = re.findall(pattern, text)
        return [c for c in candidates if len(c) >= 4 and len(c) <= 8][:10]

    def _extract_dates(self, text: str) -> List[str]:
        patterns = [
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b\d{2}-\d{2}-\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
        dates = []
        for p in patterns:
            dates.extend(re.findall(p, text))
        return dates[:5]

    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        pattern = r'(?:Rs\.?|INR|₹)?\s*([0-9,]+\.?[0-9]{0,2})'
        matches = re.findall(pattern, text)
        amounts = []
        for m in matches:
            clean = m.replace(",", "")
            try:
                val = float(clean)
                if val > 100:  # Filter out noise
                    amounts.append({"value": val, "currency": "INR"})
            except:
                continue
        return amounts[:10]

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        pattern = r'(?:Invoice No|Inv #|Bill No)[:\s]*([A-Z0-9/-]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
