from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "RAG Service"
    pinecone_api_key: Optional[str] = None
    pinecone_index: str = "accounting-legal-docs"
    pinecone_namespace: str = "indian_tax"
    elasticsearch_url: str = "http://elasticsearch:9200"
    postgres_url: str = "postgresql://user:pass@postgres:5432/accounting"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hybrid_alpha: float = 0.7  # Weight for dense vs sparse
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    class Config:
        env_file = ".env"

settings = Settings()
