from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./waymark.db"
    jwt_secret: str = "dev-only-change-me-0123456789abcdef0123"
    access_minutes: int = 30
    refresh_days: int = 7
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000"
    scheduler_enabled: bool = False  # tests keep it off; make dev turns it on
    alert_cycle_minutes: int = 5
    login_max_attempts: int = 10  # per email per 5 min


settings = Settings()
