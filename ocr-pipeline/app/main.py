from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import io
import boto3
from PIL import Image

from app.core.config import settings
from app.core.logging import logger
from app.classifiers.document_classifier import DocumentClassifier
from app.extractors.ocr_engine import OCREngine
from app.validators.validation_engine import ValidationEngine

app = FastAPI(
    title="OCR Pipeline - Document Processing",
    description="Computer vision, OCR, and validation for accounting documents",
    version="1.0.0"
)

classifier = DocumentClassifier()
ocr_engine = OCREngine()
validator = ValidationEngine()

class OCRResponse(BaseModel):
    document_id: str
    doc_type: str
    classification_confidence: float
    pages: List[Dict[str, Any]]
    extracted_data: Dict[str, Any]
    validation_result: Dict[str, Any]
    duplicates_detected: List[Dict[str, Any]]
    s3_key: str
    status: str

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ocr-pipeline"}

@app.post("/process", response_model=OCRResponse)
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client_id: str = "",
    document_id: Optional[str] = None
):
    """Process an uploaded document: classify, OCR, extract, validate."""
    doc_id = document_id or f"doc_{client_id}_{int(time.time())}"

    try:
        content = await file.read()

        # Upload to S3 (background)
        s3_key = f"{client_id}/{doc_id}/{file.filename}"
        # background_tasks.add_task(upload_to_s3, content, s3_key)  # Simplified

        # Classify
        if file.content_type and file.content_type.startswith("image/"):
            image = Image.open(io.BytesIO(content))
            classification = await classifier.classify(image)
            ocr_result = ocr_engine.extract_from_image(image)
            pages = [ocr_result]
        elif file.content_type == "application/pdf":
            classification = {"doc_type": "unknown", "confidence": 0.0}  # PDF classification needs first page
            pages = ocr_engine.extract_from_pdf(content)
            if pages:
                first_page = Image.open(io.BytesIO(content))  # Simplified - would extract first page
                classification = await classifier.classify(first_page)
        else:
            raise HTTPException(400, "Unsupported file type. Use PDF or image.")

        # Extract structured data from all pages
        all_text = "\n".join([p["raw_text"] for p in pages])
        structured = ocr_engine.extract_structured(all_text)

        # Validate
        validation = validator.validate_document(structured)

        # Check duplicates (simplified - would query DB in production)
        duplicates = []

        return OCRResponse(
            document_id=doc_id,
            doc_type=classification["doc_type"],
            classification_confidence=classification["confidence"],
            pages=pages,
            extracted_data=structured,
            validation_result=validation,
            duplicates_detected=duplicates,
            s3_key=s3_key,
            status="completed" if validation["valid"] else "needs_review"
        )

    except Exception as e:
        logger.error("ocr_processing_failed", doc_id=doc_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

import time

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
