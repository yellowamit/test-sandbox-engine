import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://sandbox_user:sandbox_secret@localhost:5433/sandbox_test_db"
    )
    APP_ENV: str = os.getenv("APP_ENV", "test")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))

settings = Settings()
