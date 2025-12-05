"""Configuration management for MCP Server"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8085
    environment: str = "development"
    debug: bool = False

    # Security
    mcp_api_key: str
    secret_key: str

    # Database
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "mcp"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    database_url: Optional[str] = None

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: Optional[str] = None

    # External Integrations
    adp_api_url: Optional[str] = None
    adp_client_id: Optional[str] = None
    adp_client_secret: Optional[str] = None

    netsuite_api_url: Optional[str] = None
    netsuite_account: Optional[str] = None
    netsuite_consumer_key: Optional[str] = None
    netsuite_consumer_secret: Optional[str] = None
    netsuite_token_key: Optional[str] = None
    netsuite_token_secret: Optional[str] = None

    dentalintel_api_url: Optional[str] = None
    dentalintel_api_key: Optional[str] = None
    dentalintel_api_secret: Optional[str] = None

    eaglesoft_api_url: Optional[str] = None
    eaglesoft_api_key: Optional[str] = None
    eaglesoft_api_secret: Optional[str] = None

    dentrix_api_url: Optional[str] = None
    dentrix_api_key: Optional[str] = None
    dentrix_api_secret: Optional[str] = None

    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_password: Optional[str] = None
    snowflake_warehouse: Optional[str] = None
    snowflake_database: Optional[str] = None
    snowflake_schema: Optional[str] = None
    snowflake_role: Optional[str] = None

    # Key-pair authentication (recommended for production)
    snowflake_private_key_path: Optional[str] = None
    snowflake_private_key_passphrase: Optional[str] = None

    # AI/LLM
    openai_api_key: Optional[str] = None

    # CORS
    cors_origins: str = "*"  # Comma-separated list of allowed origins

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # MCP
    temporal_host: str = "temporal:7233"
    temporal_namespace: str = "default"

    @property
    def allowed_origins(self) -> list[str]:
        """Get list of allowed CORS origins"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def db_url(self) -> str:
        """Get database URL"""
        if self.database_url:
            return self.database_url
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def cache_url(self) -> str:
        """Get Redis URL"""
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
