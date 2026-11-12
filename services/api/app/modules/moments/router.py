# app/modules/moments/router.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.db import db_cursor
from app.core.timeutil import to_iso_utc
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/moments", tags=["Moments 动态广场与主页信息流"])

MOMENT_COLUMNS = """
    m.id, m.username, m.content, m.created_at,
    COALESCE(u.nickname, m.username), COALESCE(u.avatar_url, '👤')
"""


class MomentCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=280)


def serialize_moment(row) -> dict:
    """将动态查询结果行序列化为前端需要的结构。"""
    return {
        "id": row[0],
        "username": row[1],
        "content": row[2],
        "time": to_iso_utc(row[3]),
        "nickname": row[4],
        "avatar": row[5],
    }


@router.post("")
async def create_moment(data: MomentCreateSchema, current_user: dict = Depends(get_current_user)):
    with db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO moments (username, content) VALUES (%s, %s)",
            (current_user["username"], data.content.strip()),
        )
    return {"success": True, "message": "动态发布成功"}


@router.get("")
async def get_all_moments(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """推荐流：全平台动态（分页）。"""
    with db_cursor() as cur:
        cur.execute(
            f"SELECT {MOMENT_COLUMNS} FROM moments m JOIN users u ON m.username = u.username "
            "ORDER BY m.created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        records = cur.fetchall()
    return {"success": True, "moments": [serialize_moment(r) for r in records]}


@router.get("/following")
async def get_following_moments(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """关注流：仅本人及已同意好友的动态（分页）。"""
    username = current_user["username"]
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT {MOMENT_COLUMNS}
            FROM moments m
            JOIN users u ON m.username = u.username
            WHERE m.username IN (
                SELECT CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END
                FROM friendships f
                WHERE (f.username = %s OR f.friend_username = %s) AND f.status = 'accepted'
            ) OR m.username = %s
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (username, username, username, username, limit, offset),
        )
        records = cur.fetchall()
    return {"success": True, "moments": [serialize_moment(r) for r in records]}


@router.get("/user/{target_username}")
async def get_user_moments(
    target_username: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    with db_cursor() as cur:
        cur.execute(
            f"SELECT {MOMENT_COLUMNS} FROM moments m JOIN users u ON m.username = u.username "
            "WHERE m.username = %s ORDER BY m.created_at DESC LIMIT %s OFFSET %s",
            (target_username, limit, offset),
        )
        records = cur.fetchall()
    return {"success": True, "moments": [serialize_moment(r) for r in records]}


@router.get("/count")
async def get_new_moments_count(since: str, current_user: dict = Depends(get_current_user)):
    """统计 since 之后新发布的动态数量（用于主页“新动态”气泡）。"""
    try:
        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="since 参数必须是 ISO 8601 时间字符串")
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM moments WHERE created_at > %s", (since_dt,))
        count = cur.fetchone()[0]
    return {"success": True, "count": count}
