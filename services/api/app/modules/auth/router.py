# app/modules/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.db import db_cursor
from .service import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth 身份验证模块"])


class UserAuthSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=30)


class ProfileUpdateSchema(BaseModel):
    nickname: str = Field(..., max_length=20)
    avatar_url: str = Field(...)


@router.post("/register")
async def register(user: UserAuthSchema):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="该用户名已被注册")

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (user.username, hash_password(user.password)),
        )
    return {"success": True, "message": "注册成功，请登录"}


@router.post("/login")
async def login(user: UserAuthSchema):
    with db_cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (user.username,))
        record = cur.fetchone()

    if not record or not verify_password(user.password, record[0]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    return {
        "success": True,
        "access_token": create_access_token(user.username),
        "token_type": "bearer",
    }


@router.post("/profile")
async def update_profile(data: ProfileUpdateSchema, current_user: dict = Depends(get_current_user)):
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET nickname = %s, avatar_url = %s WHERE username = %s",
            (data.nickname.strip(), data.avatar_url.strip(), current_user["username"]),
        )
    return {"success": True, "message": "个人资料更新成功"}


@router.get("/profile/{target_username}")
async def get_user_profile(target_username: str):
    with db_cursor() as cur:
        cur.execute(
            "SELECT username, COALESCE(nickname, username), COALESCE(avatar_url, '👤') "
            "FROM users WHERE username = %s",
            (target_username,),
        )
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="该用户不存在")
    return {"success": True, "username": row[0], "nickname": row[1], "avatar": row[2]}
