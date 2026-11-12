# app/modules/search/router.py
from fastapi import APIRouter, Depends, HTTPException
from app.modules.auth.service import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/search", tags=["Search 模糊搜索模块"])

# 模糊检索全网用户列表（自动排除自己）
@router.get("/users")
async def search_users(q: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    query_str = f"%{q.strip()}%"
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT username, COALESCE(nickname, username), COALESCE(avatar_url, '👤')
            FROM users
            WHERE (username ILIKE %s OR nickname ILIKE %s) AND username != %s
            LIMIT 15
        """, (query_str, query_str, username))
        records = cur.fetchall()
        
        users = []
        for row in records:
            # 查询我与该用户之间的好友状态，以便在前端展示加好友按钮
            cur.execute("""
                SELECT status, username FROM friendships
                WHERE (username = %s AND friend_username = %s) OR (username = %s AND friend_username = %s)
            """, (username, row[0], row[0], username))
            friend_row = cur.fetchone()
            
            friend_status = "none" # 没有任何关系
            if friend_row:
                status_val = friend_row[0]
                requester = friend_row[1]
                if status_val == "accepted":
                    friend_status = "friends" # 已是好友
                else:
                    friend_status = "sent" if requester == username else "received" # 我发出的申请 或 对方发出的申请
            
            users.append({
                "username": row[0],
                "nickname": row[1],
                "avatar": row[2],
                "friend_status": friend_status
            })
            
        return {"success": True, "users": users}
    finally:
        cur.close()
        conn.close()