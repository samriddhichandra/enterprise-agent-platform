"""
Centralized app configuration, loaded from environment variables (.env).

Keeping this in one place means every module (agents, rag, database) reads
settings the same way instead of scattering os.getenv() calls everywhere.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "postgresql+asyncpg://agent_user:agent_pass@localhost:5432/agent_platform"
    chroma_persist_dir: str = "./data/chroma_store"
    docs_dir: str = "./data/sample_docs"

    # Agent / LLM behavior — pulled out of code so they can be tuned per
    # environment without touching graph.py or pipeline.py
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    top_k: int = 4
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"


settings = Settings()
