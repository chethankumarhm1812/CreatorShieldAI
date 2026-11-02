from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "local-demo-development-key-not-for-production"
    database_url: str = "sqlite:///./creatorshield.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ai_provider: str = "demo"
    openai_api_key: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def require_configured_production_secret(self):
        if self.app_env.lower() in {"prod", "production"} and self.secret_key.startswith("local-demo-"):
            raise ValueError("SECRET_KEY must be configured with a strong value in production")
        return self

settings = Settings()
