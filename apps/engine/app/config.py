from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    engine_name: str = "n1hub-engine"
    engine_version: str = "0.1.0"
    store_backend: str = "memory"
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/n1hub"
    redis_url: str = "redis://localhost:6379/0"
    rag_chunk_size: int = 800
    rag_chunk_stride: int = 200
    rag_retriever_top_k: int = 6
    rag_mmr_lambda: float = 0.3
    rag_per_source_cap: int = 3
    rag_rerank_pool: int = 24
    rag_rerank_keep: int = 8
    rag_diversity_suppression: bool = True
    answer_max_tokens: int = 350
    citation_min_conf: float = 0.62
    citation_fallback: str = "idk+dig_deep"
    evaluation_recall_min: float = 0.85
    evaluation_contextual_recall_min: float = 0.90
    evaluation_faithfulness_min: float = 0.95
    evaluation_citation_share_min: float = 0.70
    router_health_min: float = 0.80
    semantic_hash_mismatch_rate: float = 0.0
    pii_flagged_capsules: int = 0
    rate_limit_upload: int = 60
    rate_limit_chat: int = 60
    rate_limit_public: int = 120
    max_concurrent_jobs: int = 10
    max_payload_mb: int = 20
    retention_days: int = 7
    llm_provider: str = "anthropic"  # "anthropic" or "openai"
    llm_api_key: str = ""
    llm_model: str = "claude-3-haiku-20240307"  # Default for Anthropic, or "gpt-4o-mini" for OpenAI
    public_score_threshold: float = 0.62  # Score threshold for public scope
    embedding_model: str = "all-MiniLM-L6-v2"  # Sentence transformers model for embeddings
    embedding_dimension: int = 384  # Matches infra/sql/0004_update_vector_dimension.sql

    model_config = SettingsConfigDict(env_file="config/.env", env_file_encoding="utf-8", env_prefix="N1HUB_")

    @property
    def rag_defaults(self) -> dict:
        return {
            "chunk_size": self.rag_chunk_size,
            "chunk_stride": self.rag_chunk_stride,
            "retriever_top_k": self.rag_retriever_top_k,
            "mmr_lambda": self.rag_mmr_lambda,
            "per_source_cap": self.rag_per_source_cap,
            "rerank_pool": self.rag_rerank_pool,
            "rerank_keep": self.rag_rerank_keep,
            "diversity_suppression": self.rag_diversity_suppression,
            "answer_max_tokens": self.answer_max_tokens,
            "citation_min_conf": self.citation_min_conf,
            "citation_fallback": self.citation_fallback
        }


settings = Settings()
