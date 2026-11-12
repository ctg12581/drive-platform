# app/core/db.py
"""asyncpg 异步连接池、事务上下文与建表初始化。"""
import asyncio
import json

import asyncpg
import bcrypt

from app.core.config import settings

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def _init_connection(conn: asyncpg.Connection):
    """为每个连接注册 JSONB 编解码，使 JSONB 列可直接读写 Python 对象。"""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool():
    """创建全局异步连接池（在应用 lifespan 启动时调用）。"""
    global _pool
    async with _pool_lock:
        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=max(1, settings.DB_POOL_MAX_CONN),
                command_timeout=settings.DB_STATEMENT_TIMEOUT_MS / 1000,
                statement_cache_size=max(0, settings.DB_STATEMENT_CACHE_SIZE),
                init=_init_connection,
            )


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("数据库连接池尚未初始化")
    return _pool


class _ConnContext:
    """只读连接上下文：从池中借用一个连接，退出时自动归还。"""

    async def __aenter__(self) -> asyncpg.Connection:
        self._cm = get_pool().acquire()
        return await self._cm.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        return await self._cm.__aexit__(exc_type, exc, tb)


class _TxContext:
    """写事务上下文：借连接 + 开启事务，正常退出提交、异常回滚。"""

    async def __aenter__(self) -> asyncpg.Connection:
        self._conn_cm = get_pool().acquire()
        self._conn = await self._conn_cm.__aenter__()
        self._tx_cm = self._conn.transaction()
        await self._tx_cm.__aenter__()
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self._tx_cm.__aexit__(exc_type, exc, tb)
        finally:
            await self._conn_cm.__aexit__(exc_type, exc, tb)
        return False


def db_conn() -> _ConnContext:
    """只读查询用：`async with db_conn() as conn:`"""
    return _ConnContext()


def db_transaction() -> _TxContext:
    """写入用：`async with db_transaction() as conn:`"""
    return _TxContext()


# 需要统一为 TIMESTAMPTZ 的时间列（表名, 列名）
_TIMESTAMP_COLUMNS = [
    ("users", "created_at"),
    ("drive_records", "created_at"),
    ("friendships", "created_at"),
    ("chat_messages", "created_at"),
    ("moments", "created_at"),
    ("quiz_questions", "created_at"),
    ("user_quizzes", "created_at"),
    ("user_quiz_questions", "created_at"),
    ("quiz_attempts", "created_at"),
    ("hot_news", "fetched_at"),
    ("anime_works", "fetched_at"),
    ("anime_characters", "fetched_at"),
]


def _timestamp_migration_sql(table: str, column: str) -> str:
    """生成幂等的「naive timestamp -> timestamptz」迁移语句（按 UTC 解释旧值）。"""
    return f"""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = '{table}'
              AND column_name = '{column}'
              AND data_type = 'timestamp without time zone'
        ) THEN
            ALTER TABLE {table}
                ALTER COLUMN {column} TYPE TIMESTAMPTZ
                USING {column} AT TIME ZONE 'UTC';
        END IF;
    END $$;
    """


# 全平台建表与历史数据平滑迁移语句（按顺序执行，可重复运行）。
SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(100) NOT NULL,
        nickname VARCHAR(50),
        avatar_url TEXT,
        is_admin BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;",
    """
    UPDATE users SET is_admin = TRUE
    WHERE username = 'admin'
      AND NOT EXISTS (SELECT 1 FROM users WHERE is_admin = TRUE);
    """,
    """
    CREATE TABLE IF NOT EXISTS drive_records (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        d_grade CHAR(1),
        r_grade CHAR(1),
        i_grade CHAR(1),
        v_grade CHAR(1),
        e_grade CHAR(1),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 旧表兼容：早期 drive_records 没有 username 列
    "ALTER TABLE drive_records ADD COLUMN IF NOT EXISTS username VARCHAR(50);",
    """
    CREATE TABLE IF NOT EXISTS friendships (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        friend_username VARCHAR(50) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, friend_username)
    );
    """,
    "ALTER TABLE friendships ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';",
    "UPDATE friendships SET status = 'accepted' WHERE status IS NULL;",
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id SERIAL PRIMARY KEY,
        sender VARCHAR(50) NOT NULL,
        receiver VARCHAR(50) NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        is_recalled BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_recalled BOOLEAN DEFAULT FALSE;",
    """
    CREATE TABLE IF NOT EXISTS moments (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT DEFAULT '',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE moments ADD COLUMN IF NOT EXISTS image_url TEXT DEFAULT '';",
    """
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id SERIAL PRIMARY KEY,
        question_text TEXT NOT NULL,
        options JSONB NOT NULL,
        creator VARCHAR(50) DEFAULT 'admin',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE quiz_questions ADD COLUMN IF NOT EXISTS creator VARCHAR(50) DEFAULT 'admin';",
    """
    CREATE TABLE IF NOT EXISTS user_quizzes (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        title VARCHAR(100),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS user_quiz_questions (
        id SERIAL PRIMARY KEY,
        quiz_id INT REFERENCES user_quizzes(id) ON DELETE CASCADE,
        question_id INT NOT NULL,
        preset_answer CHAR(1) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(quiz_id, question_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id SERIAL PRIMARY KEY,
        quiz_id INT REFERENCES user_quizzes(id) ON DELETE CASCADE,
        respondent_username VARCHAR(50) NOT NULL,
        score FLOAT NOT NULL,
        answers JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(quiz_id, respondent_username)
    );
    """,
    # 热点新闻：由后台定时爬虫整表刷新为最新快照
    """
    CREATE TABLE IF NOT EXISTS hot_news (
        id SERIAL PRIMARY KEY,
        source VARCHAR(50) NOT NULL,
        kind VARCHAR(10) DEFAULT 'rank',
        category VARCHAR(30) DEFAULT '热点',
        title TEXT NOT NULL,
        summary TEXT DEFAULT '',
        url TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        hot BIGINT DEFAULT 0,
        external_id VARCHAR(200) DEFAULT '',
        rank_index INT DEFAULT 0,
        fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE hot_news ADD COLUMN IF NOT EXISTS kind VARCHAR(10) DEFAULT 'rank';",
    "ALTER TABLE hot_news ADD COLUMN IF NOT EXISTS image_url TEXT DEFAULT '';",
    # 动漫人物图鉴：作品表 + 角色表（作品 1 : N 角色），由后台定时爬虫整表刷新
    # 旧版是单表（无 work_id），检测到旧结构则一次性重建，数据由爬虫重新填充
    """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_schema = current_schema() AND table_name = 'anime_characters')
           AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = current_schema() AND table_name = 'anime_characters'
                     AND column_name = 'work_id') THEN
            DROP TABLE anime_characters CASCADE;
        END IF;
    END $$;
    """,
    """
    CREATE TABLE IF NOT EXISTS anime_works (
        id SERIAL PRIMARY KEY,
        external_id VARCHAR(80) NOT NULL,
        source VARCHAR(20) DEFAULT '',
        region VARCHAR(8) NOT NULL,
        title VARCHAR(200) NOT NULL,
        title_en VARCHAR(200) DEFAULT '',
        cover TEXT DEFAULT '',
        tags JSONB DEFAULT '[]'::jsonb,
        popularity INT DEFAULT 0,
        character_count INT DEFAULT 0,
        fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (source, external_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS anime_characters (
        id SERIAL PRIMARY KEY,
        external_id VARCHAR(80) NOT NULL,
        source VARCHAR(20) DEFAULT '',
        work_id INT NOT NULL REFERENCES anime_works(id) ON DELETE CASCADE,
        name VARCHAR(120) NOT NULL,
        name_en VARCHAR(160) DEFAULT '',
        avatar VARCHAR(16) DEFAULT '',
        image_url TEXT DEFAULT '',
        tags JSONB DEFAULT '[]'::jsonb,
        voice_actor VARCHAR(200) DEFAULT '',
        personality TEXT DEFAULT '',
        introduction TEXT DEFAULT '',
        quote TEXT DEFAULT '',
        popularity INT DEFAULT 0,
        fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (source, external_id)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_anime_works_region ON anime_works (region, popularity DESC);",
    "CREATE INDEX IF NOT EXISTS idx_anime_works_popularity ON anime_works (popularity DESC);",
    "CREATE INDEX IF NOT EXISTS idx_anime_characters_work ON anime_characters (work_id);",
    "CREATE INDEX IF NOT EXISTS idx_anime_characters_fetched_at ON anime_characters (fetched_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_receiver ON chat_messages (sender, receiver);",
    "CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_unread ON chat_messages (receiver, is_read);",
    "CREATE INDEX IF NOT EXISTS idx_friendships_username ON friendships (username);",
    "CREATE INDEX IF NOT EXISTS idx_friendships_friend ON friendships (friend_username);",
    "CREATE INDEX IF NOT EXISTS idx_friendships_status ON friendships (status);",
    "CREATE INDEX IF NOT EXISTS idx_moments_created_at ON moments (created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_moments_username ON moments (username);",
    "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts (quiz_id);",
    "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_respondent ON quiz_attempts (respondent_username);",
    "CREATE INDEX IF NOT EXISTS idx_drive_records_username ON drive_records (username);",
    "CREATE INDEX IF NOT EXISTS idx_user_quiz_questions_quiz ON user_quiz_questions (quiz_id);",
    "CREATE INDEX IF NOT EXISTS idx_hot_news_fetched_at ON hot_news (fetched_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_hot_news_category ON hot_news (category);",
] + [_timestamp_migration_sql(t, c) for t, c in _TIMESTAMP_COLUMNS]


async def _init_search_indexes():
    """为模糊搜索启用 pg_trgm 与 GIN 索引；扩展不可用时优雅降级，不阻断启动。"""
    try:
        async with db_conn() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_username_trgm "
                "ON users USING gin (username gin_trgm_ops);"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_nickname_trgm "
                "ON users USING gin (nickname gin_trgm_ops);"
            )
        print("✅ [DB] pg_trgm 搜索索引就绪")
    except Exception as exc:  # noqa: BLE001 - 扩展受托管方限制时降级
        print(f"⚠️ [DB] pg_trgm 搜索索引初始化跳过（搜索仍可用但为全表扫描）: {exc}")


async def _ensure_default_admin():
    """若尚无管理员且配置了 ADMIN_PASSWORD，则创建或提升初始管理员。"""
    if not settings.ADMIN_PASSWORD:
        return
    username = (settings.ADMIN_USERNAME or "admin").strip() or "admin"
    async with db_transaction() as conn:
        exists = await conn.fetchval("SELECT 1 FROM users WHERE is_admin = TRUE LIMIT 1")
        if exists:
            return
        row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
        if row:
            await conn.execute("UPDATE users SET is_admin = TRUE WHERE username = $1", username)
            print(f"✅ [DB] 已将既有账号 {username} 提升为管理员")
        else:
            password_hash = bcrypt.hashpw(
                settings.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            await conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES ($1, $2, TRUE)",
                username,
                password_hash,
            )
            print(f"✅ [DB] 已创建初始管理员 {username}")


async def init_global_tables():
    """在服务启动时统一建表、索引与历史数据迁移。失败会抛出以便启动阶段暴露问题。"""
    async with db_conn() as conn:
        for idx, statement in enumerate(SCHEMA_STATEMENTS):
            try:
                await conn.execute(statement)
            except Exception as exc:  # noqa: BLE001 - 打印具体失败语句便于定位
                snippet = " ".join(statement.split())[:160]
                print(f"❌ [DB] 迁移语句 #{idx} 失败: {snippet!r} :: {exc}")
                raise
    await _init_search_indexes()
    await _ensure_default_admin()
    print("✅ [DB] 数据库表结构初始化成功")
