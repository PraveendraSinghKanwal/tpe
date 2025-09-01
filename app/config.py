from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    app_name: str = Field(default="AI-Powered Backend", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Database Settings
    database_url: str = Field(env="DATABASE_URL")
    database_url_sync: str = Field(env="DATABASE_URL_SYNC")
    
    # OpenAI Settings
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    
    # Okta Settings
    okta_issuer: str = Field(env="OKTA_ISSUER")
    okta_client_id: str = Field(env="OKTA_CLIENT_ID")
    okta_client_secret: str = Field(env="OKTA_CLIENT_SECRET")
    okta_audience: str = Field(env="OKTA_AUDIENCE")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
