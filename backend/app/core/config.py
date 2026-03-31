from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BasketCompare API"
    debug: bool = False
    database_url: str = "postgresql+psycopg2://basket:password@postgres:5432/basketcompare"
    redis_url: str = "redis://redis:6379/0"
    enable_embeddings: bool = False


settings = Settings()
