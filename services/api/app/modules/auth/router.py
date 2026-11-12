# app/modules/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.core.db import db_conn, db_transaction
from .service import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth 身份验证模块"])


class UserAuthSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=30)


class ProfileUpdateSchema(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=20)
    avatar_url: str = Field(..., max_length=2048)


@router.post("/register")
async def register(user: UserAuthSchema):
    # 'admin' 为系统保留账号，禁止通过公开注册抢占（管理员由 ADMIN_PASSWORD 引导）
    if user.username.lower() == "admin":
        raise HTTPException(status_code=400, detail="该用户名为系统保留，无法注册")

    async with db_transaction() as conn:
        exists = await conn.fetchval("SELECT id FROM users WHERE username = $1", user.username)
        if exists:
            raise HTTPException(status_code=400, detail="该用户名已被注册")
        password_hash = await run_in_threadpool(hash_password, user.password)
        await conn.execute(
            "INSERT INTO users (username, password_hash) VALUES ($1, $2)",
            user.username,
            password_hash,
        )
    return {"success": True, "message": "注册成功，请登录"}


@router.post("/login")
async def login(user: UserAuthSchema):
    async with db_conn() as conn:
        record = await conn.fetchrow(
            "SELECT password_hash FROM users WHERE username = $1", user.username
        )

    if not record or not await run_in_threadpool(verify_password, user.password, record[0]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    return {
        "success": True,
        "access_token": create_access_token(user.username),
        "token_type": "bearer",
    }


@router.post("/profile")
async def update_profile(data: ProfileUpdateSchema, current_user: dict = Depends(get_current_user)):
    async with db_transaction() as conn:
        await conn.execute(
            "UPDATE users SET nickname = $1, avatar_url = $2 WHERE username = $3",
            data.nickname.strip(),
            data.avatar_url.strip(),
            current_user["username"],
        )
    return {"success": True, "message": "个人资料更新成功"}


@router.get("/profile/{target_username}")
async def get_user_profile(target_username: str):
    async with db_conn() as conn:
        row = await conn.fetchrow(
            "SELECT username, COALESCE(nickname, username), COALESCE(avatar_url, '👤') "
            "FROM users WHERE username = $1",
            target_username,
        )

    if not row:
        raise HTTPException(status_code=404, detail="该用户不存在")
    return {"success": True, "username": row[0], "nickname": row[1], "avatar": row[2]}
