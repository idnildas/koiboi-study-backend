from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Koiboi Study Backend"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./dev.db"

    class Config:
        env_file = ".env"


settings = Settings()
