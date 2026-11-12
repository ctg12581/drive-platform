# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = ""
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365 

    # 💡 核心修改一：在 Settings 类中明确声明这 5 个 R2 变量。
    # 这样 Pydantic 就会正常识别并载入它们，同时允许您在全站通过 settings 极简读取！
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    # Pydantic v2 标准配置字典
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # 💡 核心修改二：强力保险！允许并忽略 .env 中的其他多余变量，绝对不再报 Extra inputs 错误
    )

settings = Settings()