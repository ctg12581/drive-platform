# app/core/db.py
"""数据库连接池、游标上下文与建表初始化。"""
import threading
from contextlib import contextmanager

import bcrypt
import psycopg2
from psycopg2 import pool

from app.core.config import settings

_pool = None
_pool_lock = threading.Lock()


def get_pool() -> pool.ThreadedConnectionPool:
    """惰性创建线程安全连接池（FastAPI 同步端点在线程池中执行）。"""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pool.ThreadedConnectionPool(
                    1,
                    max(1, settings.DB_POOL_MAX_CONN),
                    dsn=settings.DATABASE_URL,
                    connect_timeout=10,
                    options=f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS}",
                )
    return _pool


def get_db_connection():
    """保留旧接口：从连接池取一个连接（调用方需自行归还）。"""
    return get_pool().getconn()


@contextmanager
def db_cursor(commit: bool = False):
    """数据库游标上下文管理器（连接来自连接池）。

    统一处理连接的提交 / 回滚与归还，替代每个接口里重复的
    try/finally 样板代码。异常会自动回滚。
    """
    conn = get_pool().getconn()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        get_pool().putconn(conn)


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
    # 1. 用户表（含管理员标志）
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
    # 历史账号兼容：若库中尚无管理员，则将名为 admin 的既有账号提升为管理员（仅引导一次）
    """
    UPDATE users SET is_admin = TRUE
    WHERE username = 'admin'
      AND NOT EXISTS (SELECT 1 FROM users WHERE is_admin = TRUE);
    """,
    # 2. 人格评测记录表
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
    # 3. 双向好友关系表
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
    # 4. 聊天消息表
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
    # 5. 动态广场表
    """
    CREATE TABLE IF NOT EXISTS moments (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 6. 公共默契度题库表
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
    # 7. 用户出题主表
    """
    CREATE TABLE IF NOT EXISTS user_quizzes (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        title VARCHAR(100),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 8. 用户预设答案表
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
    # 9. 挑战历史表
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
    # 10. 高频查询索引
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
] + [_timestamp_migration_sql(t, c) for t, c in _TIMESTAMP_COLUMNS]


def _ensure_default_admin():
    """若尚无管理员且配置了 ADMIN_PASSWORD，则创建或提升初始管理员。"""
    if not settings.ADMIN_PASSWORD:
        return
    username = (settings.ADMIN_USERNAME or "admin").strip() or "admin"
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT 1 FROM users WHERE is_admin = TRUE LIMIT 1")
        if cur.fetchone():
            return
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.execute("UPDATE users SET is_admin = TRUE WHERE username = %s", (username,))
            print(f"✅ [DB] 已将既有账号 {username} 提升为管理员")
        else:
            password_hash = bcrypt.hashpw(
                settings.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cur.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (%s, %s, TRUE)",
                (username, password_hash),
            )
            print(f"✅ [DB] 已创建初始管理员 {username}")


def _init_search_indexes():
    """为模糊搜索启用 pg_trgm 与 GIN 索引；扩展不可用时优雅降级，不阻断启动。"""
    try:
        with db_cursor(commit=True) as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_username_trgm "
                "ON users USING gin (username gin_trgm_ops);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_nickname_trgm "
                "ON users USING gin (nickname gin_trgm_ops);"
            )
        print("✅ [DB] pg_trgm 搜索索引就绪")
    except Exception as exc:  # noqa: BLE001 - 扩展受托管方限制时降级
        print(f"⚠️ [DB] pg_trgm 搜索索引初始化跳过（搜索仍可用但为全表扫描）: {exc}")


def init_global_tables():
    """在服务启动时统一建表、索引与历史数据迁移。失败会抛出以便启动阶段暴露问题。"""
    with db_cursor(commit=True) as cur:
        for statement in SCHEMA_STATEMENTS:
            cur.execute(statement)
    _init_search_indexes()
    _ensure_default_admin()
    print("✅ [DB] 数据库表结构初始化成功")
