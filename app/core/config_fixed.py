"""
完全简化的配置文件，避免所有导入问题
"""

from typing import Optional, List

class Settings:
    """
    🔒 完全简化的应用配置
    """

    def __init__(self):
        # ============================================
        # 📱 Application Configuration
        # ============================================
        self.app_name = "Async AI Task Runner"
        self.app_version = "0.1.0"
        self.debug = False
        self.environment = "development"

        # ============================================
        # 🔐 Security Configuration
        # ============================================
        self.secret_key = None

        # ============================================
        # 🗄️ Database Configuration
        # ============================================
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.db_pool_size = 10
        self.db_max_overflow = 20
        self.db_pool_timeout = 30

        # ============================================
        # 🔴 Redis Configuration
        # ============================================
        self.redis_url = "redis://localhost:6379/0"
        self.redis_pool_size = 20
        self.redis_pool_timeout = 10

        # ============================================
        # ⚙ Celery Configuration
        # ============================================
        self.celery_broker_url = "redis://localhost:6379/1"
        self.celery_result_backend = "redis://localhost:6379/2"
        self.worker_concurrency = 4
        self.worker_prefetch_multiplier = 1
        self.worker_max_tasks_per_child = 1000

        # ============================================
        # 🤖 AI Service Configuration
        # ============================================
        self.openai_api_key = None
        self.openai_base_url = "https://api.openai.com/v1"
        self.anthropic_api_key = None
        self.anthropic_base_url = "https://api.anthropic.com"
        self.deepseek_api_key = None
        self.deepseek_base_url = "https://api.deepseek.com"
        self.default_ai_model = "gpt-3.5-turbo"
        self.ai_temperature = 0.7
        self.ai_max_tokens = 1000

        # ============================================
        # 🌐 Server Configuration
        # ============================================
        self.api_v1_str = "/api/v1"
        self.host = "0.0.0.0"
        self.port = 8000

        # ============================================
        # 📊 Monitoring Configuration
        # ============================================
        self.log_level = "INFO"
        self.show_sql_queries = False
        self.flower_port = 5555
        self.flower_basic_auth_user = "admin"
        self.flower_basic_auth_password = "admin"

        # ============================================
        # 🚦 Rate Limiting Configuration
        # ============================================
        self.rate_limit_requests_per_minute = 100
        self.rate_limit_upload_size_mb = 10

        # ============================================
        # 🕐 Timezone Configuration
        # ============================================
        self.timezone = "Asia/Shanghai"

        # ============================================
        # 🛠️ Development Configuration
        # ============================================
        self.auto_reload = True
        self.enable_profiling = False

        # ============================================
        # 🧪 Test Configuration
        # ============================================
        self.test_database_url = None

        # ============================================
        # 📡 CORS Configuration
        # ============================================
        @property
        def cors_origins(self) -> List[str]:
            """CORS 配置"""
            return ["http://localhost:8000", "http://localhost:3000"]

# 创建全局实例
settings = Settings()