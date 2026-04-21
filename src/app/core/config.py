from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Koiboi Study Backend"
    DEBUG: bool = True
    # Use an async postgres URL by default for development if no .env provided
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/koiboi_db"

    class Config:
        env_file = ".env"


settings = Settings()
