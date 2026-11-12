# app/modules/search/router.py
from fastapi import APIRouter, Depends

from app.core.db import db_cursor
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/search", tags=["Search 模糊搜索模块"])


def resolve_friend_status(status: str | None, requester: str | None, current_username: str) -> str:
    """将双方关系记录转换为前端展示状态。"""
    if not status:
        return "none"
    if status == "accepted":
        return "friends"
    return "sent" if requester == current_username else "received"


@router.get("/users")
def search_users(q: str, current_user: dict = Depends(get_current_user)):
    """模糊检索全网用户（排除自己），并带上与当前用户的好友关系状态。"""
    username = current_user["username"]
    query_str = f"%{q.strip()}%"

    with db_cursor() as cur:
        # 单次查询完成用户检索 + 关系状态关联，避免逐用户查询的 N+1 问题
        cur.execute(
            """
            SELECT u.username, COALESCE(u.nickname, u.username), COALESCE(u.avatar_url, '👤'),
                   f.status, f.username
            FROM users u
            LEFT JOIN friendships f
                   ON (f.username = u.username AND f.friend_username = %s)
                   OR (f.friend_username = u.username AND f.username = %s)
            WHERE (u.username ILIKE %s OR u.nickname ILIKE %s) AND u.username != %s
            LIMIT 15
            """,
            (username, username, query_str, query_str, username),
        )
        records = cur.fetchall()

    users = [
        {
            "username": row[0],
            "nickname": row[1],
            "avatar": row[2],
            "friend_status": resolve_friend_status(row[3], row[4], username),
        }
        for row in records
    ]
    return {"success": True, "users": users}
