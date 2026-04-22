from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Application Configuration
    APP_NAME: str = Field(default="Koiboi Study Backend")
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8080)

    # Database Configuration (Required)
    DATABASE_URL: str = Field(
        description="PostgreSQL database URL with asyncpg driver"
    )

    # JWT Configuration (Required)
    JWT_SECRET: str = Field(
        description="Secret key for JWT token signing (minimum 32 characters)"
    )
    JWT_EXPIRATION_HOURS: int = Field(default=24)

    # Cloud Storage Configuration
    STORAGE_TYPE: str = Field(default="s3", description="Storage backend: s3 or gcs")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_S3_BUCKET: Optional[str] = Field(default=None)
    AWS_REGION: Optional[str] = Field(default="us-east-1")

    # Email Service Configuration
    EMAIL_SERVICE: str = Field(default="sendgrid", description="Email service: sendgrid or ses")
    SENDGRID_API_KEY: Optional[str] = Field(default=None)
    SENDGRID_FROM_EMAIL: Optional[str] = Field(default=None)

    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60)

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")

    # Redis Configuration (Optional)
    REDIS_URL: Optional[str] = Field(default=None)

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT_SECRET is at least 32 characters."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator("STORAGE_TYPE")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        """Validate STORAGE_TYPE is either s3 or gcs."""
        if v not in ("s3", "gcs"):
            raise ValueError("STORAGE_TYPE must be either 's3' or 'gcs'")
        return v

    @field_validator("EMAIL_SERVICE")
    @classmethod
    def validate_email_service(cls, v: str) -> str:
        """Validate EMAIL_SERVICE is either sendgrid or ses."""
        if v not in ("sendgrid", "ses"):
            raise ValueError("EMAIL_SERVICE must be either 'sendgrid' or 'ses'")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate LOG_LEVEL is one of the allowed values."""
        allowed_levels = ("DEBUG", "INFO", "WARNING", "ERROR")
        if v not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate LOG_FORMAT is either json or text."""
        if v not in ("json", "text"):
            raise ValueError("LOG_FORMAT must be either 'json' or 'text'")
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS_ORIGINS is a non-empty comma-separated list."""
        if not v or not v.strip():
            raise ValueError("CORS_ORIGINS cannot be empty")
        return v

    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Create settings instance - this will validate all environment variables on startup
try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Failed to load configuration. Please check your environment variables: {str(e)}"
    ) from e
