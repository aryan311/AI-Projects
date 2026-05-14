from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """TraceLab application settings, configurable via environment variables."""

    # SQLite run store
    sqlite_db_path: str = "tracelab.db"

    # Ollama LLM
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:latest"

    # OpenTelemetry
    otel_exporter_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "tracelab"
    enable_tracing: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
