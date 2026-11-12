# app/modules/moments/router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.modules.auth.service import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/moments", tags=["Moments 动态广场与主页信息流"])

class MomentCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=280)

# 1. 发布新动态 (主页发帖)
@router.post("")
async def create_moment(data: MomentCreateSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO moments (username, content) VALUES (%s, %s)", (username, data.content.strip()))
        conn.commit()
        return {"success": True, "message": "动态发布成功"}
    finally:
        cur.close()
        conn.close()

# 2. 推荐流 (For You)：展示全平台所有动态
@router.get("")
async def get_all_moments():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.id, m.username, m.content, m.created_at, 
                   COALESCE(u.nickname, m.username), COALESCE(u.avatar_url, '👤')
            FROM moments m
            JOIN users u ON m.username = u.username
            ORDER BY m.created_at DESC
        """)
        records = cur.fetchall()
        moments = []
        for row in records:
            moments.append({
                "id": row[0],
                "username": row[1],
                "content": row[2],
                "time": row[3].isoformat() + "Z",
                "nickname": row[4],
                "avatar": row[5]
            })
        return {"success": True, "moments": moments}
    finally:
        cur.close()
        conn.close()

# 3. 💡 新增：关注流 (Following)：仅展示我已同意好友（以及我自己）的动态
@router.get("/following")
async def get_following_moments(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 只查询双方关系已被接受且是我自己或已同意好友的动态
        cur.execute("""
            SELECT m.id, m.username, m.content, m.created_at, 
                   COALESCE(u.nickname, m.username), COALESCE(u.avatar_url, '👤')
            FROM moments m
            JOIN users u ON m.username = u.username
            WHERE m.username IN (
                SELECT CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END
                FROM friendships f
                WHERE (f.username = %s OR f.friend_username = %s) AND f.status = 'accepted'
            ) OR m.username = %s
            ORDER BY m.created_at DESC
        """, (username, username, username, username))
        records = cur.fetchall()
        moments = []
        for row in records:
            moments.append({
                "id": row[0],
                "username": row[1],
                "content": row[2],
                "time": row[3].isoformat() + "Z",
                "nickname": row[4],
                "avatar": row[5]
            })
        return {"success": True, "moments": moments}
    finally:
        cur.close()
        conn.close()

# 4. 获取指定某人的历史动态
@router.get("/user/{target_username}")
async def get_user_moments(target_username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.id, m.username, m.content, m.created_at, 
                   COALESCE(u.nickname, m.username), COALESCE(u.avatar_url, '👤')
            FROM moments m
            JOIN users u ON m.username = u.username
            WHERE m.username = %s
            ORDER BY m.created_at DESC
        """, (target_username,))
        records = cur.fetchall()
        moments = []
        for row in records:
            moments.append({
                "id": row[0],
                "username": row[1],
                "content": row[2],
                "time": row[3].isoformat() + "Z",
                "nickname": row[4],
                "avatar": row[5]
            })
        return {"success": True, "moments": moments}
    finally:
        cur.close()
        conn.close()

# 5. 💡 新增：获取自某个时间点后，新发布动态的数量（用于在主页显示“新推文”气泡）
@router.get("/count")
async def get_new_moments_count(since: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # since 为 ISO-8601 标准字符串，如 "2026-06-27T06:10:00Z"
        cur.execute("SELECT COUNT(*) FROM moments WHERE created_at > %s", (since,))
        count = cur.fetchone()[0]
        return {"success": True, "count": count}
    finally:
        cur.close()
        conn.close()