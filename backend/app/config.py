from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://cereborate:password@localhost:5432/cereborate"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    llm_backend: str = "ollama"  # ollama | vllm
    llm_base_url: str = "http://localhost:11434/v1"
    llm_planning_model: str = "qwen3:8b"
    llm_classifier_model: str = "qwen3:1.7b"
    llm_embedding_model: str = "nomic-embed-text"

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # App
    app_env: str = "development"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
