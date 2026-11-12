# app/modules/search/router.py
from fastapi import APIRouter, Depends

from app.core.db import db_conn
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
async def search_users(q: str, current_user: dict = Depends(get_current_user)):
    """模糊检索全网用户（排除自己），并带上与当前用户的好友关系状态。"""
    username = current_user["username"]
    query_str = f"%{q.strip()}%"

    async with db_conn() as conn:
        # 单次查询完成用户检索 + 关系状态关联，避免逐用户查询的 N+1 问题
        records = await conn.fetch(
            """
            SELECT u.username, COALESCE(u.nickname, u.username), COALESCE(u.avatar_url, '👤'),
                   f.status, f.username
            FROM users u
            LEFT JOIN friendships f
                   ON (f.username = u.username AND f.friend_username = $1)
                   OR (f.friend_username = u.username AND f.username = $1)
            WHERE (u.username ILIKE $3 OR u.nickname ILIKE $3) AND u.username != $2
            LIMIT 15
            """,
            username,
            username,
            query_str,
        )

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
