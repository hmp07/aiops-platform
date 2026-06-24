from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "AIOps Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aiops:aiops@postgres:5432/aiops"
    DATABASE_SYNC_URL: str = "postgresql://aiops:aiops@postgres:5432/aiops"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CELERY_BROKER_URL: str = "redis://redis:6379/1"
    REDIS_CELERY_RESULT_URL: str = "redis://redis:6379/2"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_CONFIG: str = "config-backups"
    MINIO_BUCKET_REPORTS: str = "inspection-reports"
    MINIO_SECURE: bool = False

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # LLM
    LLM_PROVIDER: str = "anthropic"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Agent
    AGENT_MAX_ITERATIONS: int = 15
    AGENT_TIMEOUT_SECONDS: int = 300
    AGENT_APPROVAL_TIMEOUT_SECONDS: int = 120

    # External Systems
    ITOP_API_URL: str = ""
    ITOP_API_USER: str = ""
    ITOP_API_PASSWORD: str = ""
    ZABBIX_API_URL: str = ""
    ZABBIX_API_USER: str = ""
    ZABBIX_API_PASSWORD: str = ""
    SIGNOZ_API_URL: str = ""
    SIGNOZ_API_KEY: str = ""

    # Notification
    WECOM_WEBHOOK_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Data Collection
    ITEM_SYNC_INTERVAL_MINUTES: int = 60
    ARP_SYNC_INTERVAL_MINUTES: int = 15
    METRIC_COLLECT_INTERVAL_MINUTES: int = 5
    CONFIG_BACKUP_TIME: str = "02:00"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
