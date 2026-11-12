# app/modules/admin/router.py
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.db import db_cursor
from app.core.timeutil import to_iso_utc
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin 后台管理模块"])


def get_current_admin(current_user: dict = Depends(get_current_user)):
    """仅允许数据库 is_admin 为真的账号访问后台接口。"""
    with db_cursor() as cur:
        cur.execute("SELECT is_admin FROM users WHERE username = %s", (current_user["username"],))
        row = cur.fetchone()
    if not row or not row[0]:
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
def get_dashboard_stats():
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM moments")
        total_moments = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM quiz_questions WHERE creator = 'admin'")
        total_questions = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM quiz_attempts")
        total_attempts = cur.fetchone()[0]

    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_moments": total_moments,
            "total_questions": total_questions,
            "total_attempts": total_attempts,
        },
    }


@router.get("/quiz/questions", dependencies=[Depends(get_current_admin)])
def admin_get_questions():
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, question_text, options FROM quiz_questions "
            "WHERE creator = 'admin' ORDER BY id DESC"
        )
        records = cur.fetchall()
    return {
        "success": True,
        "questions": [{"id": r[0], "text": r[1], "options": r[2]} for r in records],
    }


@router.post("/quiz/questions", dependencies=[Depends(get_current_admin)])
def admin_create_question(data: AdminQuestionSchema):
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO quiz_questions (question_text, options, creator)
            VALUES (%s, %s, 'admin')
            RETURNING id
            """,
            (data.question_text.strip(), json.dumps(data.options, ensure_ascii=False)),
        )
        question_id = cur.fetchone()[0]
    return {
        "success": True,
        "question_id": question_id,
        "message": "公共题目已成功加入系统题库",
    }


@router.delete("/quiz/questions/{question_id}", dependencies=[Depends(get_current_admin)])
def admin_delete_question(question_id: int):
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            DELETE FROM quiz_questions
            WHERE id = %s AND (creator = 'admin' OR creator = 'system' OR creator IS NULL)
            """,
            (question_id,),
        )
    return {"success": True, "message": "公共题目已成功从系统题库中删除"}


@router.get("/users", dependencies=[Depends(get_current_admin)])
def admin_get_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """用户监控列表：先分组聚合近 3 类计数，再一次性关联，避免逐用户子查询。"""
    with db_cursor() as cur:
        cur.execute(
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
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        records = cur.fetchall()

    total = records[0][8] if records else 0
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
def admin_bulk_import_questions(data: BulkImportSchema):
    try:
        with db_cursor(commit=True) as cur:
            for question in data.questions:
                cur.execute(
                    """
                    INSERT INTO quiz_questions (question_text, options, creator)
                    VALUES (%s, %s, 'admin')
                    """,
                    (question.question_text.strip(), json.dumps(question.options, ensure_ascii=False)),
                )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"批量导入异常: {exc}") from exc
    return {"success": True, "message": f"成功批量导入 {len(data.questions)} 道系统公共题目"}
