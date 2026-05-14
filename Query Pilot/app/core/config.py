from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://querypilot:querypilot_password@localhost:5432/querypilot_db"
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:latest"
    
    # Query execution limits
    max_query_timeout_seconds: float = 5.0
    max_row_limit: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
