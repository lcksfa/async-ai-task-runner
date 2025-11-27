from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, validator
import secrets


class Settings(BaseSettings):
    """
    🔒 安全配置管理类
    使用环境变量管理所有敏感配置，避免硬编码
    """

    # ============================================
    # 📱 Application Configuration
    # ============================================

    app_name: str = Field(default="Async AI Task Runner", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development/staging/production)")

    # ============================================
    # 🔐 Security Configuration
    # ============================================

    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Application secret key"
    )

    # CORS Configuration
    cors_origins_str: str = Field(
        default="http://localhost:8000",
        description="CORS allowed origins (comma-separated)",
        alias="cors_origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")

    # ============================================
    # 🗄️ Database Configuration
    # ============================================

    database_url: str = Field(
        default="postgresql+asyncpg://taskuser:taskpass@localhost:5433/task_runner",
        description="Database connection URL"
    )

    # Database Pool Configuration
    db_pool_size: int = Field(default=10, description="Database pool size")
    db_max_overflow: int = Field(default=20, description="Database max overflow")
    db_pool_timeout: int = Field(default=30, description="Database pool timeout")

    # ============================================
    # 🔴 Redis Configuration
    # ============================================

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Redis Pool Configuration
    redis_pool_size: int = Field(default=20, description="Redis pool size")
    redis_pool_timeout: int = Field(default=10, description="Redis pool timeout")

    # ============================================
    # ⚡ Celery Configuration
    # ============================================

    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )

    # Worker Configuration
    worker_concurrency: int = Field(default=4, description="Celery worker concurrency")
    worker_prefetch_multiplier: int = Field(default=1, description="Worker prefetch multiplier")
    worker_max_tasks_per_child: int = Field(default=1000, description="Max tasks per worker child")

    # Task Configuration
    task_default_retry_delay: int = Field(default=60, description="Default task retry delay (seconds)")
    task_max_retries: int = Field(default=3, description="Maximum task retry attempts")
    task_soft_time_limit: int = Field(default=300, description="Task soft time limit (seconds)")
    task_time_limit: int = Field(default=600, description="Task hard time limit (seconds)")
    task_result_expires: int = Field(default=3600, description="Task result expiration time (seconds)")

    # ============================================
    # 🤖 AI Service Configuration
    # ============================================

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI API base URL")

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_base_url: str = Field(default="https://api.anthropic.com", description="Anthropic API base URL")

    # DeepSeek Configuration
    deepseek_api_key: Optional[str] = Field(default=None, description="DeepSeek API key")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", description="DeepSeek API base URL")

    # AI Model Configuration
    default_ai_model: str = Field(default="gpt-3.5-turbo", description="Default AI model")
    ai_temperature: float = Field(default=0.7, description="AI temperature parameter")
    ai_max_tokens: int = Field(default=1000, description="AI max tokens")

    # ============================================
    # 🌐 Server Configuration
    # ============================================

    api_v1_str: str = Field(default="/api/v1", description="API version 1 path")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # ============================================
    # 📊 Monitoring & Logging
    # ============================================

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    show_sql_queries: bool = Field(default=False, description="Show SQL queries in logs")

    # Flower Configuration
    flower_port: int = Field(default=5555, description="Flower monitoring port")
    flower_basic_auth_user: str = Field(default="admin", description="Flower basic auth user")
    flower_basic_auth_password: str = Field(
        default_factory=lambda: secrets.token_urlsafe(16),
        description="Flower basic auth password"
    )

    # Health Check Configuration
    health_check_interval: int = Field(default=30, description="Health check interval")

    # ============================================
    # 🛡️ Rate Limiting
    # ============================================

    rate_limit_requests_per_minute: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_upload_size_mb: int = Field(default=10, description="Rate limit upload size (MB)")

    # ============================================
    # 🌐 Timezone Configuration
    # ============================================

    timezone: str = Field(default="Asia/Shanghai", description="Application timezone")

    # ============================================
    # 🔗 Development Configuration
    # ============================================

    # Development Features
    auto_reload: bool = Field(default=True, description="Enable auto reload")
    enable_profiling: bool = Field(default=False, description="Enable profiling")

    # Test Configuration
    test_database_url: Optional[str] = Field(
        default=None,
        description="Test database connection URL"
    )

    @validator("secret_key", pre=True)
    def validate_secret_key(cls, v: Optional[str]) -> str:
        """验证 secret_key 长度和复杂性"""
        if v is None:
            raise ValueError("SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("cors_origins_str", pre=True)
    def validate_cors_origins(cls, v: str) -> str:
        """验证 CORS origins 格式"""
        if not v:
            raise ValueError("At least one CORS origin must be specified")
        return v

    @property
    def cors_origins(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    @validator("environment", pre=True)
    def validate_environment(cls, v: str) -> str:
        """验证环境变量值"""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(allowed_envs)}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量


# 全局设置实例
settings = Settings()