# app/core/config.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 固定以 services/api/.env 为准，不依赖启动时的 CWD
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """集中管理环境变量配置（读取 services/api/.env）。"""

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    # 默认 7 天（原为 365 天，过长且不可吊销）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 数据库连接池上限（每个进程），避免每请求新建连接
    DB_POOL_MAX_CONN: int = 10

    # 逗号分隔的额外允许跨域来源，追加到内置白名单之后
    FRONTEND_ORIGINS: str = ""

    # 初始管理员引导：若库中尚无 is_admin 用户，且设置了 ADMIN_PASSWORD，
    # 启动时会自动创建（或提升）该管理员账号。生产环境务必通过环境变量配置。
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""

    # Cloudflare R2 对象存储（用于头像 / 图片上传）
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    # 图片上传大小上限（字节），默认 5MB
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        extra="ignore",
    )


settings = Settings()
