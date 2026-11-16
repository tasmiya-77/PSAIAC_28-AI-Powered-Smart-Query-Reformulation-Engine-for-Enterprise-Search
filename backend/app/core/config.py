from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Smart Query Reformulation Engine"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ChromaDB Settings
    CHROMADB_PATH: str = "./data/chroma"
    CHROMADB_COLLECTION_NAME: str = "query_reformulation_db"

    # AI & Embeddings Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Dynamic Multi-LLM Query Reformulation (Free-Quota Only)
    REFORMULATION_PROVIDER_ORDER: str = "groq,cloudflare,gemini,ollama"
    REFORMULATION_TIMEOUT_SECONDS: float = 5.0
    REFORMULATION_MAX_RETRIES: int = 1

    # Groq Settings (Free Tier: llama-3.1-8b-instant)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Cloudflare Workers AI Settings (Free Tier: @cf/meta/llama-3.1-8b-instruct)
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    CLOUDFLARE_API_TOKEN: Optional[str] = None
    CLOUDFLARE_MODEL: str = "@cf/meta/llama-3.1-8b-instruct"

    # Local Ollama Settings (Local Free: qwen2.5:3b)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    # Optional SambaNova Settings (Optional due to rate limits)
    SAMBANOVA_API_KEY: Optional[str] = None
    SAMBANOVA_MODEL: str = "Meta-Llama-3.1-8B-Instruct"
    SAMBANOVA_BASE_URL: str = "https://api.sambanova.ai/v1"

    # Security & Auth Settings
    JWT_SECRET: str = "dev_enterprise_jwt_secret_key_2026_change_in_prod"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    EMPLOYEE_USERNAME: str = "employee"
    EMPLOYEE_PASSWORD: str = "employee123"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]


settings = Settings()
