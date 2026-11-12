# app/core/db.py (全新干净版，彻底移除了默认题植入逻辑，直接覆盖保存)
import os
import psycopg2
from app.core.config import settings

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(settings.DATABASE_URL)

def init_global_tables():
    """
    在服务启动时，统一检查并初始化全平台所需的所有数据表，
    并执行高安全性的历史数据平滑迁移（确保数据库结构升级时存量数据绝对不丢）。
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. 创建/更新用户表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(100) NOT NULL,
                nickname VARCHAR(50),
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50);")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;")

        # 2. 创建/更新人格评测记录表
        cur.execute("""
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
        """)

        # 3. 创建/更新双向好友审核关系表 (添加 status 字段)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS friendships (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL, 
                friend_username VARCHAR(50) NOT NULL, 
                status VARCHAR(20) DEFAULT 'pending', 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, friend_username)
            );
        """)
        cur.execute("ALTER TABLE friendships ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';")

        # 数据修复迁移
        cur.execute("UPDATE friendships SET status = 'accepted' WHERE status IS NULL;")

        # 4. 创建/更新聊天历史消息表 (安全增加已读状态列和逻辑删除列)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                sender VARCHAR(50) NOT NULL,
                receiver VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                is_recalled BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;")
        cur.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_recalled BOOLEAN DEFAULT FALSE;")

        # 5. 创建 𝕏 动态广场表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS moments (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. 公共默契度题库表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id SERIAL PRIMARY KEY,
                question_text TEXT NOT NULL,
                options JSONB NOT NULL,
                creator VARCHAR(50) DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("ALTER TABLE quiz_questions ADD COLUMN IF NOT EXISTS creator VARCHAR(50) DEFAULT 'admin';")

        # 7. 用户出题主表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_quizzes (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                title VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 8. 用户预设答案表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_quiz_questions (
                id SERIAL PRIMARY KEY,
                quiz_id INT REFERENCES user_quizzes(id) ON DELETE CASCADE,
                question_id INT NOT NULL,
                preset_answer CHAR(1) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(quiz_id, question_id)
            );
        """)

        # 9. 挑战历史表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                quiz_id INT REFERENCES user_quizzes(id) ON DELETE CASCADE,
                respondent_username VARCHAR(50) NOT NULL,
                score FLOAT NOT NULL,
                answers JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(quiz_id, respondent_username)
            );
        """)

        conn.commit()
        print("✅ [DB] 数据库表结构初始化全部成功！已剔除默认题目的注入逻辑")
    except Exception as e:
        print(f"❌ [DB] 数据库表初始化失败: {e}")
    finally:
        cur.close()
        conn.close()