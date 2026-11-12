# app/core/db.py
"""数据库连接、游标上下文与建表初始化。"""
from contextlib import contextmanager

import psycopg2

from app.core.config import settings


def get_db_connection():
    """创建一个新的 PostgreSQL 连接。"""
    return psycopg2.connect(settings.DATABASE_URL)


@contextmanager
def db_cursor(commit: bool = False):
    """数据库游标上下文管理器。

    统一处理连接的提交 / 回滚与资源释放，替代每个接口里重复的
    try/finally/close 样板代码。异常会自动回滚。

    Args:
        commit: 为 True 时在正常退出时提交事务；纯读操作保持 False 即可。
    """
    conn = get_db_connection()
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
        conn.close()


# 全平台建表与历史数据平滑迁移语句（按顺序执行，可重复运行）。
SCHEMA_STATEMENTS = [
    # 1. 用户表
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(100) NOT NULL,
        nickname VARCHAR(50),
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;",
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 3. 双向好友关系表
    """
    CREATE TABLE IF NOT EXISTS friendships (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        friend_username VARCHAR(50) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 6. 公共默契度题库表
    """
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id SERIAL PRIMARY KEY,
        question_text TEXT NOT NULL,
        options JSONB NOT NULL,
        creator VARCHAR(50) DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "ALTER TABLE quiz_questions ADD COLUMN IF NOT EXISTS creator VARCHAR(50) DEFAULT 'admin';",
    # 7. 用户出题主表
    """
    CREATE TABLE IF NOT EXISTS user_quizzes (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        title VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 8. 用户预设答案表
    """
    CREATE TABLE IF NOT EXISTS user_quiz_questions (
        id SERIAL PRIMARY KEY,
        quiz_id INT REFERENCES user_quizzes(id) ON DELETE CASCADE,
        question_id INT NOT NULL,
        preset_answer CHAR(1) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(quiz_id, respondent_username)
    );
    """,
]


def init_global_tables():
    """在服务启动时统一建表并执行幂等的历史数据迁移。"""
    try:
        with db_cursor(commit=True) as cur:
            for statement in SCHEMA_STATEMENTS:
                cur.execute(statement)
        print("✅ [DB] 数据库表结构初始化成功")
    except Exception as exc:  # noqa: BLE001 - 启动阶段需要打印而不是崩溃
        print(f"❌ [DB] 数据库表初始化失败: {exc}")
