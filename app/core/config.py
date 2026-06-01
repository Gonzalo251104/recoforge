from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    app_name: str = "RecoForge"
    environment: str = "dev"
    database_url: str = "sqlite:///./recoforge.db"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    db_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
