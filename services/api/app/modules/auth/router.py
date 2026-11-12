# app/modules/auth/router.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from app.core.db import get_db_connection
from .service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth 身份验证模块"])

# 输入参数校验模型
class UserAuthSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=30)

@router.post("/register")
async def register(user: UserAuthSchema):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 检查用户名是否已存在
        cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="该用户名已被注册")
        
        # 密码加密并写入数据库
        pwd_hash = hash_password(user.password)
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (user.username, pwd_hash))
        conn.commit()
        return {"success": True, "message": "注册成功，请登录"}
    finally:
        cur.close()
        conn.close()

@router.post("/login")
async def login(user: UserAuthSchema):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (user.username,))
        record = cur.fetchone()
        if not record or not verify_password(user.password, record[0]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
        
        # 验证成功，签发 Token 令牌
        token = create_access_token(user.username)
        return {"success": True, "access_token": token, "token_type": "bearer"}
    finally:
        cur.close()
        conn.close()

# app/modules/auth/router.py 的底部追加以下代码：

class ProfileUpdateSchema(BaseModel):
    nickname: str = Field(..., max_length=20)
    avatar_url: str = Field(...)

# 1. 提交更新我自己的头像和昵称
@router.post("/profile")
async def update_profile(data: ProfileUpdateSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET nickname = %s, avatar_url = %s WHERE username = %s",
            (data.nickname.strip(), data.avatar_url.strip(), username)
        )
        conn.commit()
        return {"success": True, "message": "个人资料更新成功"}
    finally:
        cur.close()
        conn.close()

# 2. 获取指定用户的公开基本资料（供他人点击头像时查看）
@router.get("/profile/{target_username}")
async def get_user_profile(target_username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT username, COALESCE(nickname, username), COALESCE(avatar_url, '👤') FROM users WHERE username = %s",
            (target_username,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="该用户不存在")
        return {
            "success": True,
            "username": row[0],
            "nickname": row[1],
            "avatar": row[2]
        }
    finally:
        cur.close()
        conn.close()