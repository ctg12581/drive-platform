# app/modules/quiz/router.py
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.modules.auth.service import get_current_user
from app.core.db import get_db_connection

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
    options: list[str] # 必须包含4个选项，如 ["A. ...", "B. ...", ...]

# 1. 💡 升级：获取可选题库 (自动合并“系统公共题库”和“我自己创建的私有题目”)
@router.get("/questions")
async def get_available_questions(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, question_text, options, creator 
            FROM quiz_questions 
            WHERE creator = 'admin' OR creator = 'system' OR creator = %s 
            ORDER BY id ASC
        """, (username,))
        records = cur.fetchall()
        questions = []
        for r in records:
            questions.append({
                "id": r[0],
                "text": r[1],
                "options": r[2],
                "creator": r[3]
            })
        return {"success": True, "questions": questions}
    finally:
        cur.close()
        conn.close()

# 2. 💡 新增：用户在出题页面，实时自主创建新题目入库 (安全隔离为私有)
@router.post("/questions")
async def create_custom_question(data: CreateQuestionSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO quiz_questions (question_text, options, creator)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (data.question_text.strip(), json.dumps(data.options, ensure_ascii=False), username))
        q_id = cur.fetchone()[0]
        conn.commit()
        return {"success": True, "question_id": q_id, "message": "自定义问题已加入您的私人题库"}
    finally:
        cur.close()
        conn.close()

# 3. 💡 新增：安全拉取我出的测验配置以及对应的正确答案（用于出题页面的编辑回显，拒绝向外泄露）
@router.get("/my-config")
async def get_my_quiz_config(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM user_quizzes WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row:
            return {"success": True, "has_quiz": False}
        
        quiz_id = row[0]
        title = row[1]
        
        # 查询我出过的所有问题、选项和我的预设正确答案
        cur.execute("""
            SELECT uqq.question_id, qq.question_text, qq.options, uqq.preset_answer
            FROM user_quiz_questions uqq
            JOIN quiz_questions qq ON uqq.question_id = qq.id
            WHERE uqq.quiz_id = %s
            ORDER BY uqq.question_id ASC
        """, (quiz_id,))
        records = cur.fetchall()
        
        questions = []
        for r in records:
            questions.append({
                "id": r[0],
                "text": r[1],
                "options": r[2],
                "answer": r[3] # 💡 包含正确答案
            })
        return {
            "success": True,
            "has_quiz": True,
            "title": title,
            "questions": questions
        }
    finally:
        cur.close()
        conn.close()

# 4. 用户出题（保存/更新我的测验）
@router.post("/create")
async def create_user_quiz(data: CreateQuizSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO user_quizzes (username, title) 
            VALUES (%s, %s)
            ON CONFLICT (username) 
            DO UPDATE SET title = EXCLUDED.title 
            RETURNING id
        """, (username, data.title.strip()))
        quiz_id = cur.fetchone()[0]

        cur.execute("DELETE FROM user_quiz_questions WHERE quiz_id = %s", (quiz_id,))

        for q in data.questions:
            cur.execute("""
                INSERT INTO user_quiz_questions (quiz_id, question_id, preset_answer)
                VALUES (%s, %s, %s)
            """, (quiz_id, q.question_id, q.answer.upper()))
        
        conn.commit()
        return {"success": True, "message": "测验配置成功！"}
    finally:
        cur.close()
        conn.close()

# 5. 一键获取所有好友的测验列表与得分
@router.get("/friends-list")
async def get_friends_quizzes(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT uq.id, uq.username, uq.title, COALESCE(u.nickname, uq.username), COALESCE(u.avatar_url, '👤')
            FROM user_quizzes uq
            JOIN users u ON uq.username = u.username
            WHERE uq.username IN (
                SELECT CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END
                FROM friendships f
                WHERE (f.username = %s OR f.friend_username = %s) AND f.status = 'accepted'
            )
        """, (username, username, username))
        records = cur.fetchall()
        
        quizzes = []
        for row in records:
            quiz_id = row[0]
            friend_username = row[1]
            title = row[2]
            nickname = row[3]
            avatar = row[4]
            
            cur.execute("""
                SELECT score FROM quiz_attempts 
                WHERE quiz_id = %s AND respondent_username = %s
            """, (quiz_id, username))
            attempt_row = cur.fetchone()
            
            already_challenged = attempt_row is not None
            score = attempt_row[0] if already_challenged else 0.0
            
            quizzes.append({
                "quiz_id": quiz_id,
                "username": friend_username,
                "title": title,
                "nickname": nickname,
                "avatar": avatar,
                "already_challenged": already_challenged,
                "score": score
            })
        return {"success": True, "quizzes": quizzes}
    finally:
        cur.close()
        conn.close()

# 6. 查看某个指定用户的测验题目 (不含正确答案)
@router.get("/user/{target_username}")
async def get_user_quiz(target_username: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM user_quizzes WHERE username = %s", (target_username,))
        quiz_row = cur.fetchone()
        if not quiz_row:
            return {"success": True, "has_quiz": False}
        
        quiz_id = quiz_row[0]
        quiz_title = quiz_row[1]

        cur.execute("""
            SELECT uqq.question_id, qq.question_text, qq.options
            FROM user_quiz_questions uqq
            JOIN quiz_questions qq ON uqq.question_id = qq.id
            WHERE uqq.quiz_id = %s
            ORDER BY uqq.question_id ASC
        """, (quiz_id,))
        records = cur.fetchall()
        
        questions = []
        for r in records:
            questions.append({
                "id": r[0],
                "text": r[1],
                "options": r[2]
            })

        cur.execute("SELECT score FROM quiz_attempts WHERE quiz_id = %s AND respondent_username = %s", (quiz_id, username))
        attempt_row = cur.fetchone()
        already_challenged = attempt_row is not None
        score = attempt_row[0] if already_challenged else 0

        return {
            "success": True,
            "has_quiz": True,
            "quiz_id": quiz_id,
            "title": quiz_title,
            "questions": questions,
            "already_challenged": already_challenged,
            "score": score
        }
    finally:
        cur.close()
        conn.close()

# 7. 提交答题卡并计算默契度
@router.post("/submit")
async def submit_quiz_answers(data: SubmitAnswersSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT question_id, preset_answer FROM user_quiz_questions WHERE quiz_id = %s", (data.quiz_id,))
        records = cur.fetchall()
        if not records:
            raise HTTPException(status_code=404, detail="未找到该测验的问题配置")

        preset_map = {str(r[0]): r[1] for r in records}
        
        total_questions = len(preset_map)
        correct_count = 0
        for q_id, my_ans in data.answers.items():
            if q_id in preset_map and my_ans.upper() == preset_map[q_id]:
                correct_count += 1

        score = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0

        cur.execute("""
            INSERT INTO quiz_attempts (quiz_id, respondent_username, score, answers)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (quiz_id, respondent_username)
            DO UPDATE SET score = EXCLUDED.score, answers = EXCLUDED.answers
        """, (data.quiz_id, username, score, json.dumps(data.answers, ensure_ascii=False)))
        
        conn.commit()
        return {
            "success": True,
            "score": score,
            "total_questions": total_questions,
            "correct_count": correct_count
        }
    finally:
        cur.close()
        conn.close()