# app/modules/admin/router.py
import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.db import db_cursor
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin 后台管理模块"])


async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """仅允许 username 为 admin 的管理员访问后台接口。"""
    if current_user["username"] != "admin":
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
async def admin_get_questions():
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
async def admin_create_question(data: AdminQuestionSchema):
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
async def admin_delete_question(question_id: int):
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
async def admin_get_users():
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.username, COALESCE(u.nickname, u.username),
                   COALESCE(u.avatar_url, '👤'), u.created_at,
                   (SELECT COUNT(*) FROM moments WHERE username = u.username) AS posts_count,
                   (SELECT COUNT(*) FROM drive_records WHERE username = u.username) AS drive_count,
                   (SELECT COUNT(*) FROM quiz_attempts WHERE respondent_username = u.username) AS attempts_count
            FROM users u
            ORDER BY u.created_at DESC
            """
        )
        records = cur.fetchall()

    users = [
        {
            "id": r[0],
            "username": r[1],
            "nickname": r[2],
            "avatar": r[3],
            "created_at": r[4].isoformat() + "Z",
            "posts_count": r[5],
            "drive_count": r[6],
            "attempts_count": r[7],
        }
        for r in records
    ]
    return {"success": True, "users": users}


@router.post("/quiz/questions/bulk", dependencies=[Depends(get_current_admin)])
async def admin_bulk_import_questions(data: BulkImportSchema):
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
