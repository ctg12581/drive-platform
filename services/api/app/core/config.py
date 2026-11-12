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

    # 数据库连接池上限（每个进程），需与 FastAPI 线程池规模匹配
    DB_POOL_MAX_CONN: int = 20
    # 单条 SQL 超时（毫秒），防止慢查询长期占用连接
    DB_STATEMENT_TIMEOUT_MS: int = 15000
    # asyncpg 预编译语句缓存大小（asyncpg 默认 100）。
    # 若使用 pgbouncer / Neon 的 -pooler 连接串（事务池模式），必须设为 0，否则会报
    # "prepared statement ... already exists"。直连 Neon 主库保持默认即可。
    DB_STATEMENT_CACHE_SIZE: int = 100

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

    # 热点新闻定时爬取：是否启用，以及抓取间隔（分钟）
    NEWS_CRAWL_ENABLED: bool = True
    NEWS_CRAWL_INTERVAL_MINUTES: int = 15

    # 动漫图鉴定时爬取：是否启用、抓取间隔（分钟）
    # MAX_PER_REGION = 0 表示「不限制角色总数」，尽可能多抓；正整数则按该值截断
    ANIME_CRAWL_ENABLED: bool = True
    # 动漫资料变化很慢，默认 7 天刷新一次即可（可用环境变量覆盖）
    ANIME_CRAWL_INTERVAL_MINUTES: int = 10080
    ANIME_CRAWL_MAX_PER_REGION: int = 0
    # AniList 每个地区最多翻多少页（每页 10 部作品 × 10 个角色，30 页约 300 部作品/地区）
    ANIME_CRAWL_MAX_PAGES_PER_REGION: int = 30
    # 每部动画抓取的角色数（AniList）
    ANIME_CRAWL_CHARS_PER_MEDIA: int = 10
    # 每部美漫剧集抓取的角色数（TVmaze）
    ANIME_CRAWL_MAX_CAST_PER_SHOW: int = 20

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        extra="ignore",
    )


settings = Settings()
