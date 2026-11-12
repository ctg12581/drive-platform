# app/modules/drive/router.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.modules.auth.service import get_current_user # 引入安全守卫
from app.core.db import get_db_connection

router = APIRouter(prefix="/drive", tags=["DRIVE 人格分析"])

class DriveEvaluateRequest(BaseModel):
    d: str = Field(..., pattern="^[SABCDsabcd]$")
    r: str = Field(..., pattern="^[SABCDsabcd]$")
    i: str = Field(..., pattern="^[SABCDsabcd]$")
    v: str = Field(..., pattern="^[SABCDsabcd]$")
    e: str = Field(..., pattern="^[SABCDsabcd]$")

@router.post("/evaluate")
async def evaluate(data: DriveEvaluateRequest, current_user: dict = Depends(get_current_user)):
    """
    此接口通过 Depends(get_current_user) 进行了保护。
    前端请求时，Header 必须带有: Authorization: Bearer <你的JWT-Token>
    否则直接返回 401 Unauthorized。
    """
    username = current_user["username"] # 从登录态中获取用户名
    
    # ... 此处为您原本的得分、文本解析计算逻辑 ...
    scores = {"d": 3, "r": 4, "i": 5, "v": 4, "e": 3} # 模拟计算
    
    # 写入带有用户归属的评测记录
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO drive_records (username, d_grade, r_grade, i_grade, v_grade, e_grade) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, data.d.upper(), data.r.upper(), data.i.upper(), data.v.upper(), data.e.upper())
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {
        "success": True,
        "evaluated_for": username,
        "scores": scores,
        "synthesis": "您的各项维度均衡，请继续保持优势。"
    }