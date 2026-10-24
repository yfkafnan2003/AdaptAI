from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AdaptAI"
    openai_api_key: str = ""
    openai_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5433/adaptai"

    @property
    def plain_database_url(self) -> str:
        # Mem0 wants a plain postgresql:// URL, without the SQLAlchemy driver suffix
        return self.database_url.replace("+psycopg", "", 1)

settings = Settings()

