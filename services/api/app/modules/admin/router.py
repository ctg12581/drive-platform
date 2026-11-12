# app/modules/admin/router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.db import db_conn, db_transaction
from app.core.timeutil import to_iso_utc
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin 后台管理模块"])


async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """仅允许数据库 is_admin 为真的账号访问后台接口。"""
    async with db_conn() as conn:
        is_admin = await conn.fetchval(
            "SELECT is_admin FROM users WHERE username = $1", current_user["username"]
        )
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是系统管理员，无权访问后台管理系统",
        )
    return current_user


class AdminQuestionSchema(BaseModel):
    question_text: str = Field(...)
    options: list[str]


class BulkImportSchema(BaseModel):
    questions: list[AdminQuestionSchema]


@router.get("/dashboard/stats", dependencies=[Depends(get_current_admin)])
async def get_dashboard_stats():
    async with db_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT
              (SELECT COUNT(*) FROM users) AS total_users,
              (SELECT COUNT(*) FROM moments) AS total_moments,
              (SELECT COUNT(*) FROM quiz_questions WHERE creator = 'admin') AS total_questions,
              (SELECT COUNT(*) FROM quiz_attempts) AS total_attempts
            """
        )

    return {
        "success": True,
        "stats": {
            "total_users": row["total_users"],
            "total_moments": row["total_moments"],
            "total_questions": row["total_questions"],
            "total_attempts": row["total_attempts"],
        },
    }


@router.get("/quiz/questions", dependencies=[Depends(get_current_admin)])
async def admin_get_questions():
    async with db_conn() as conn:
        records = await conn.fetch(
            "SELECT id, question_text, options FROM quiz_questions "
            "WHERE creator = 'admin' ORDER BY id DESC"
        )
    return {
        "success": True,
        "questions": [{"id": r[0], "text": r[1], "options": r[2]} for r in records],
    }


@router.post("/quiz/questions", dependencies=[Depends(get_current_admin)])
async def admin_create_question(data: AdminQuestionSchema):
    async with db_transaction() as conn:
        question_id = await conn.fetchval(
            """
            INSERT INTO quiz_questions (question_text, options, creator)
            VALUES ($1, $2, 'admin')
            RETURNING id
            """,
            data.question_text.strip(),
            data.options,
        )
    return {
        "success": True,
        "question_id": question_id,
        "message": "公共题目已成功加入系统题库",
    }


@router.delete("/quiz/questions/{question_id}", dependencies=[Depends(get_current_admin)])
async def admin_delete_question(question_id: int):
    async with db_transaction() as conn:
        await conn.execute(
            """
            DELETE FROM quiz_questions
            WHERE id = $1 AND (creator = 'admin' OR creator = 'system' OR creator IS NULL)
            """,
            question_id,
        )
    return {"success": True, "message": "公共题目已成功从系统题库中删除"}


@router.get("/users", dependencies=[Depends(get_current_admin)])
async def admin_get_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """用户监控列表：先分组聚合近 3 类计数，再一次性关联，避免逐用户子查询。"""
    async with db_conn() as conn:
        records = await conn.fetch(
            """
            WITH moment_cnt AS (
                SELECT username, COUNT(*) AS cnt FROM moments GROUP BY username
            ),
            drive_cnt AS (
                SELECT username, COUNT(*) AS cnt FROM drive_records GROUP BY username
            ),
            attempt_cnt AS (
                SELECT respondent_username AS username, COUNT(*) AS cnt
                FROM quiz_attempts GROUP BY respondent_username
            )
            SELECT u.id, u.username, COALESCE(u.nickname, u.username),
                   COALESCE(u.avatar_url, '👤'), u.created_at,
                   COALESCE(mc.cnt, 0), COALESCE(dc.cnt, 0), COALESCE(ac.cnt, 0),
                   COUNT(*) OVER() AS total
            FROM users u
            LEFT JOIN moment_cnt mc ON mc.username = u.username
            LEFT JOIN drive_cnt dc ON dc.username = u.username
            LEFT JOIN attempt_cnt ac ON ac.username = u.username
            ORDER BY u.created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

    total = records[0]["total"] if records else 0
    users = [
        {
            "id": r[0],
            "username": r[1],
            "nickname": r[2],
            "avatar": r[3],
            "created_at": to_iso_utc(r[4]),
            "posts_count": r[5],
            "drive_count": r[6],
            "attempts_count": r[7],
        }
        for r in records
    ]
    return {"success": True, "users": users, "total": total}


@router.post("/quiz/questions/bulk", dependencies=[Depends(get_current_admin)])
async def admin_bulk_import_questions(data: BulkImportSchema):
    try:
        async with db_transaction() as conn:
            for question in data.questions:
                await conn.execute(
                    """
                    INSERT INTO quiz_questions (question_text, options, creator)
                    VALUES ($1, $2, 'admin')
                    """,
                    question.question_text.strip(),
                    question.options,
                )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"批量导入异常: {exc}") from exc
    return {"success": True, "message": f"成功批量导入 {len(data.questions)} 道系统公共题目"}
