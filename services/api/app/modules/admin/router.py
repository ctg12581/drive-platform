# app/modules/admin/router.py
import json
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel, Field
from app.modules.auth.service import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/admin", tags=["Admin 后台管理模块"])

# 💡 安全守卫：强制要求只有 username 为 'admin' 的管理员才能访问
async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user["username"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="您不是系统管理员，无权访问后台管理系统"
        )
    return current_user

class AdminQuestionSchema(BaseModel):
    question_text: str = Field(...)
    options: list[str] # 必须是包含 2~4 个选项的字符串数组

# 1. 仪表盘：获取全系统大盘数据汇总
@router.get("/dashboard/stats", dependencies=[Depends(get_current_admin)])
async def get_dashboard_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
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
                "total_attempts": total_attempts
            }
        }
    finally:
        cur.close()
        conn.close()

# 2. 题库管理：获取所有的公共题库
@router.get("/quiz/questions", dependencies=[Depends(get_current_admin)])
async def admin_get_questions():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, question_text, options FROM quiz_questions WHERE creator = 'admin' ORDER BY id DESC")
        records = cur.fetchall()
        questions = [{"id": r[0], "text": r[1], "options": r[2]} for r in records]
        return {"success": True, "questions": questions}
    finally:
        cur.close()
        conn.close()

# 3. 题库管理：添加一道新的公共题目
@router.post("/quiz/questions", dependencies=[Depends(get_current_admin)])
async def admin_create_question(data: AdminQuestionSchema):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO quiz_questions (question_text, options, creator)
            VALUES (%s, %s, 'admin')
            RETURNING id
        """, (data.question_text.strip(), json.dumps(data.options, ensure_ascii=False)))
        q_id = cur.fetchone()[0]
        conn.commit()
        return {"success": True, "question_id": q_id, "message": "公共题目已成功加入系统题库"}
    finally:
        cur.close()
        conn.close()

# 💡 升级：4. 删除系统公共题目 (支持删除任何非用户自定义的系统内置题目)
@router.delete("/quiz/questions/{question_id}", dependencies=[Depends(get_current_admin)])
async def admin_delete_question(question_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 支持强行抹除任何属于 admin、system 或空标识的内置系统题
        cur.execute("""
            DELETE FROM quiz_questions 
            WHERE id = %s AND (creator = 'admin' OR creator = 'system' OR creator IS NULL)
        """, (question_id,))
        conn.commit()
        return {"success": True, "message": "公共题目已成功从系统题库中删除"}
    finally:
        cur.close()
        conn.close()

# 5. 用户数据监控：获取全网所有用户的注册信息及活跃维度统计
@router.get("/users", dependencies=[Depends(get_current_admin)])
async def admin_get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 高级 SQL 联合统计：查出用户的头像、昵称、注册时间，并统计发帖数、人格分析次数、默契挑战次数
        cur.execute("""
            SELECT u.id, u.username, COALESCE(u.nickname, u.username), COALESCE(u.avatar_url, '👤'), u.created_at,
                   (SELECT COUNT(*) FROM moments WHERE username = u.username) as posts_count,
                   (SELECT COUNT(*) FROM drive_records WHERE username = u.username) as drive_count,
                   (SELECT COUNT(*) FROM quiz_attempts WHERE respondent_username = u.username) as attempts_count
            FROM users u
            ORDER BY u.created_at DESC
        """)
        records = cur.fetchall()
        users = []
        for r in records:
            users.append({
                "id": r[0],
                "username": r[1],
                "nickname": r[2],
                "avatar": r[3],
                "created_at": r[4].isoformat() + "Z",
                "posts_count": r[5],
                "drive_count": r[6],
                "attempts_count": r[7]
            })
        return {"success": True, "users": users}
    finally:
        cur.close()
        conn.close()


class BulkImportSchema(BaseModel):
    # 接收一个由题目组成的数组列表
    questions: list[AdminQuestionSchema]

# 💡 新增：一键批量导入公共题库 API (无任何额外重量级依赖，Render 秒部署)
@router.post("/quiz/questions/bulk", dependencies=[Depends(get_current_admin)])
async def admin_bulk_import_questions(data: BulkImportSchema):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 批量循环写入公共题库
        for q in data.questions:
            cur.execute("""
                INSERT INTO quiz_questions (question_text, options, creator)
                VALUES (%s, %s, 'admin')
            """, (q.question_text.strip(), json.dumps(q.options, ensure_ascii=False)))
        conn.commit()
        return {"success": True, "message": f"成功批量导入 {len(data.questions)} 道系统公共题目"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量导入异常: {e}")
    finally:
        cur.close()
        conn.close()