# app/modules/quiz/router.py
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.db import db_cursor
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/quiz", tags=["Quiz 恋爱默契度大挑战"])


class QuizQuestionAnswer(BaseModel):
    question_id: int
    answer: str = Field(..., pattern="^[ABCD]$")


class CreateQuizSchema(BaseModel):
    title: str = Field(..., max_length=50)
    questions: list[QuizQuestionAnswer]


class SubmitAnswersSchema(BaseModel):
    quiz_id: int
    answers: dict[str, str]


class CreateQuestionSchema(BaseModel):
    question_text: str = Field(..., min_length=1)
    options: list[str]


@router.get("/questions")
async def get_available_questions(current_user: dict = Depends(get_current_user)):
    """系统公共题库 + 我创建的私有题目。"""
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT id, question_text, options, creator
            FROM quiz_questions
            WHERE creator = 'admin' OR creator = 'system' OR creator = %s
            ORDER BY id ASC
            """,
            (current_user["username"],),
        )
        records = cur.fetchall()
    return {
        "success": True,
        "questions": [
            {"id": r[0], "text": r[1], "options": r[2], "creator": r[3]} for r in records
        ],
    }


@router.post("/questions")
async def create_custom_question(data: CreateQuestionSchema, current_user: dict = Depends(get_current_user)):
    """用户自主创建私有题目。"""
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO quiz_questions (question_text, options, creator)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (data.question_text.strip(), json.dumps(data.options, ensure_ascii=False), current_user["username"]),
        )
        question_id = cur.fetchone()[0]
    return {"success": True, "question_id": question_id, "message": "自定义问题已加入您的私人题库"}


@router.get("/my-config")
async def get_my_quiz_config(current_user: dict = Depends(get_current_user)):
    """拉取我出的测验配置及正确答案（仅本人可读）。"""
    with db_cursor() as cur:
        cur.execute("SELECT id, title FROM user_quizzes WHERE username = %s", (current_user["username"],))
        row = cur.fetchone()
        if not row:
            return {"success": True, "has_quiz": False}

        quiz_id, title = row
        cur.execute(
            """
            SELECT uqq.question_id, qq.question_text, qq.options, uqq.preset_answer
            FROM user_quiz_questions uqq
            JOIN quiz_questions qq ON uqq.question_id = qq.id
            WHERE uqq.quiz_id = %s
            ORDER BY uqq.question_id ASC
            """,
            (quiz_id,),
        )
        records = cur.fetchall()

    questions = [
        {"id": r[0], "text": r[1], "options": r[2], "answer": r[3]} for r in records
    ]
    return {"success": True, "has_quiz": True, "title": title, "questions": questions}


@router.post("/create")
async def create_user_quiz(data: CreateQuizSchema, current_user: dict = Depends(get_current_user)):
    """保存 / 更新我的测验。"""
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO user_quizzes (username, title)
            VALUES (%s, %s)
            ON CONFLICT (username) DO UPDATE SET title = EXCLUDED.title
            RETURNING id
            """,
            (current_user["username"], data.title.strip()),
        )
        quiz_id = cur.fetchone()[0]

        cur.execute("DELETE FROM user_quiz_questions WHERE quiz_id = %s", (quiz_id,))
        for question in data.questions:
            cur.execute(
                """
                INSERT INTO user_quiz_questions (quiz_id, question_id, preset_answer)
                VALUES (%s, %s, %s)
                """,
                (quiz_id, question.question_id, question.answer.upper()),
            )
    return {"success": True, "message": "测验配置成功！"}


@router.get("/friends-list")
async def get_friends_quizzes(current_user: dict = Depends(get_current_user)):
    """一键获取所有好友的测验列表与我的得分。"""
    username = current_user["username"]
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT uq.id, uq.username, uq.title, COALESCE(u.nickname, uq.username),
                   COALESCE(u.avatar_url, '👤')
            FROM user_quizzes uq
            JOIN users u ON uq.username = u.username
            WHERE uq.username IN (
                SELECT CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END
                FROM friendships f
                WHERE (f.username = %s OR f.friend_username = %s) AND f.status = 'accepted'
            )
            """,
            (username, username, username),
        )
        rows = cur.fetchall()

        quizzes = []
        for row in rows:
            quiz_id, friend_username, title, nickname, avatar = row
            cur.execute(
                "SELECT score FROM quiz_attempts WHERE quiz_id = %s AND respondent_username = %s",
                (quiz_id, username),
            )
            attempt = cur.fetchone()
            quizzes.append(
                {
                    "quiz_id": quiz_id,
                    "username": friend_username,
                    "title": title,
                    "nickname": nickname,
                    "avatar": avatar,
                    "already_challenged": attempt is not None,
                    "score": attempt[0] if attempt else 0.0,
                }
            )
    return {"success": True, "quizzes": quizzes}


@router.get("/user/{target_username}")
async def get_user_quiz(target_username: str, current_user: dict = Depends(get_current_user)):
    """查看指定用户的测验题目（不含正确答案）。"""
    username = current_user["username"]
    with db_cursor() as cur:
        cur.execute("SELECT id, title FROM user_quizzes WHERE username = %s", (target_username,))
        quiz_row = cur.fetchone()
        if not quiz_row:
            return {"success": True, "has_quiz": False}

        quiz_id, quiz_title = quiz_row
        cur.execute(
            """
            SELECT uqq.question_id, qq.question_text, qq.options
            FROM user_quiz_questions uqq
            JOIN quiz_questions qq ON uqq.question_id = qq.id
            WHERE uqq.quiz_id = %s
            ORDER BY uqq.question_id ASC
            """,
            (quiz_id,),
        )
        records = cur.fetchall()

        cur.execute(
            "SELECT score FROM quiz_attempts WHERE quiz_id = %s AND respondent_username = %s",
            (quiz_id, username),
        )
        attempt = cur.fetchone()

    questions = [{"id": r[0], "text": r[1], "options": r[2]} for r in records]
    return {
        "success": True,
        "has_quiz": True,
        "quiz_id": quiz_id,
        "title": quiz_title,
        "questions": questions,
        "already_challenged": attempt is not None,
        "score": attempt[0] if attempt else 0,
    }


@router.post("/submit")
async def submit_quiz_answers(data: SubmitAnswersSchema, current_user: dict = Depends(get_current_user)):
    """提交答题卡并计算默契度。"""
    with db_cursor(commit=True) as cur:
        cur.execute(
            "SELECT question_id, preset_answer FROM user_quiz_questions WHERE quiz_id = %s",
            (data.quiz_id,),
        )
        records = cur.fetchall()
        if not records:
            raise HTTPException(status_code=404, detail="未找到该测验的问题配置")

        preset_map = {str(question_id): preset for question_id, preset in records}
        total_questions = len(preset_map)
        correct_count = sum(
            1
            for question_id, my_answer in data.answers.items()
            if question_id in preset_map and my_answer.upper() == preset_map[question_id]
        )
        score = round((correct_count / total_questions) * 100, 1) if total_questions else 0.0

        cur.execute(
            """
            INSERT INTO quiz_attempts (quiz_id, respondent_username, score, answers)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (quiz_id, respondent_username)
            DO UPDATE SET score = EXCLUDED.score, answers = EXCLUDED.answers
            """,
            (data.quiz_id, current_user["username"], score, json.dumps(data.answers, ensure_ascii=False)),
        )

    return {
        "success": True,
        "score": score,
        "total_questions": total_questions,
        "correct_count": correct_count,
    }
