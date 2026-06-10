from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "AI Orchestrator"
    debug: bool = False
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_proxy_url: str = "http://llm-gateway:8080"
    default_llm_model: str = "gpt-4o"
    rag_service_url: str = "http://rag-service:8000"
    valuation_engine_url: str = "http://valuation-engine:8000"
    guardrails_service_url: str = "http://guardrails-service:8000"
    redis_url: str = "redis://redis-cluster:6379/0"
    jaeger_endpoint: str = "http://jaeger:14268/api/traces"

    class Config:
        env_file = ".env"

settings = Settings()
