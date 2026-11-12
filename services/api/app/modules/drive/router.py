# app/modules/drive/router.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.db import db_cursor
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/drive", tags=["DRIVE 人格分析"])

# 等级到分数的映射，用于生成雷达图数据
GRADE_SCORE = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}

DIMENSION_LABELS = {
    "d": "决策力",
    "r": "意志力",
    "i": "智力",
    "v": "价值观",
    "e": "灵活性",
}


class DriveEvaluateRequest(BaseModel):
    d: str = Field(..., pattern="^[SABCDsabcd]$")
    r: str = Field(..., pattern="^[SABCDsabcd]$")
    i: str = Field(..., pattern="^[SABCDsabcd]$")
    v: str = Field(..., pattern="^[SABCDsabcd]$")
    e: str = Field(..., pattern="^[SABCDsabcd]$")


def build_synthesis(scores: dict[str, int]) -> str:
    """根据五维得分生成一句简要成长建议。"""
    average = sum(scores.values()) / len(scores)
    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)
    if average >= 4.5:
        return f"各项维度表现优异，尤其在{DIMENSION_LABELS[strongest]}上突出，请继续保持。"
    if average >= 3.5:
        return f"整体表现良好，{DIMENSION_LABELS[strongest]}是优势，可重点提升{DIMENSION_LABELS[weakest]}。"
    return f"建议优先加强{DIMENSION_LABELS[weakest]}，同时发挥{DIMENSION_LABELS[strongest]}的优势。"


@router.post("/evaluate")
async def evaluate(data: DriveEvaluateRequest, current_user: dict = Depends(get_current_user)):
    """对当前登录用户的五维等级进行评测并记录历史。"""
    username = current_user["username"]
    grades = {
        "d": data.d.upper(),
        "r": data.r.upper(),
        "i": data.i.upper(),
        "v": data.v.upper(),
        "e": data.e.upper(),
    }
    scores = {key: GRADE_SCORE[grade] for key, grade in grades.items()}

    with db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO drive_records "
            "(username, d_grade, r_grade, i_grade, v_grade, e_grade) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (username, grades["d"], grades["r"], grades["i"], grades["v"], grades["e"]),
        )

    return {
        "success": True,
        "evaluated_for": username,
        "scores": scores,
        "synthesis": build_synthesis(scores),
    }
