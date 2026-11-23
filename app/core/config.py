from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """项目配置管理"""

    # Saleor 配置
    saleor_api_url: str = "http://localhost:8000/graphql/"
    saleor_token: str = ""
    saleor_channel: str = "default-channel"

    # 大模型配置，后续使用
    llm_api_key: str = "DASHSCOPE_API_KEY"
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "deepseek-v4-flash"

    # MySQL连接信息
    mysql_host: str = "localhost"
    mysql_port: str = "3306"
    mysql_user: str = "root"
    mysql_password: str
    mysql_database: str = "saleor"

    # Redis连接信息
    redis_host: str = "localhost"
    redis_port: str = "6379"
    redis_db: int = 1

    # 邮件配置
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 587
    smtp_sender: str = ""
    smtp_user: str = ""
    smtp_password: str
    smtp_use_tls: bool = True

    # JWT配置
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # 应用配置
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
