from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
from typing import Dict, Any
from app.core.config import settings
from app.core.logging import logger

class DocumentClassifier:
    """Classify uploaded documents using vision models."""

    DOC_TYPES = ["invoice", "bank_statement", "receipt", "contract", "esg_report", "tax_notice", "audit_paper", "other"]

    def __init__(self):
        self.processor = AutoImageProcessor.from_pretrained(settings.classification_model)
        self.model = AutoModelForImageClassification.from_pretrained(settings.classification_model)
        self.model.eval()

    async def classify(self, image: Image.Image) -> Dict[str, Any]:
        """Classify a document image."""
        try:
            inputs = self.processor(image, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)
                confidence, predicted_class = torch.max(probs, 1)

            # Map to accounting doc types (simplified - in production use fine-tuned model)
            doc_type = self.DOC_TYPES[predicted_class.item() % len(self.DOC_TYPES)]

            logger.info("document_classified", doc_type=doc_type, confidence=confidence.item())
            return {
                "doc_type": doc_type,
                "confidence": round(confidence.item(), 4),
                "all_scores": {t: round(probs[0][i].item(), 4) for i, t in enumerate(self.DOC_TYPES)}
            }
        except Exception as e:
            logger.error("classification_failed", error=str(e))
            return {"doc_type": "other", "confidence": 0.0, "error": str(e)}
