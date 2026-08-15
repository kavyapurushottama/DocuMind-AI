"""
Central app configuration. All values come from environment variables
(loaded from a .env file in local dev). Nothing here is hardcoded so the
same code works in any environment.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Databases / infra ---
    DATABASE_URL: str = "postgresql://docmind:localdevpass@localhost:5432/docmind"
    REDIS_URL: str = "redis://localhost:6379"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "docmind_chunks"

    # --- Auth ---
    JWT_SECRET: str = "change-this-to-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # --- LLM / embedding providers (all free-tier) ---
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"  # "groq" or "gemini"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIM: int = 768

    EMBEDDING_PROVIDER: str = "fastembed"  # "fastembed", "gemini", or "ollama"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # --- Uploads ---
    MAX_UPLOAD_MB: int = 25
    UPLOAD_DIR: str = "./uploads"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
