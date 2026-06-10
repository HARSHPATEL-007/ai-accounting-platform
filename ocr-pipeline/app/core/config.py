from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "OCR Pipeline"
    s3_bucket: str = "accounting-docs-prod"
    aws_region: str = "ap-south-1"
    tesseract_cmd: str = "/usr/bin/tesseract"
    classification_model: str = "microsoft/resnet-50"
    extraction_model: str = "gpt-4o"  # Fallback for complex docs
    llm_proxy_url: str = "http://llm-gateway:8080"

    class Config:
        env_file = ".env"

settings = Settings()
