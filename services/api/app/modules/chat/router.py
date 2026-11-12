# app/modules/chat/router.py (完全覆盖该文件)
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict
import boto3
from botocore.config import Config
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel, Field
from app.modules.auth.service import get_current_user
from app.core.db import get_db_connection
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["Chat 实时社交与好友关系"])

R2_ACCOUNT_ID = settings.R2_ACCOUNT_ID
R2_ACCESS_KEY_ID = settings.R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY = settings.R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME = settings.R2_BUCKET_NAME
R2_PUBLIC_URL = settings.R2_PUBLIC_URL

# 初始化 Boto3 S3 兼容客户端
r2_client = None
if all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
    try:
        r2_client = boto3.client(
            service_name="s3",
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4")
        )
        print("✅ Cloudflare R2 存储客户端初始化成功")
    except Exception as e:
        print(f"❌ Cloudflare R2 存储客户端初始化失败: {e}")

class AddFriendSchema(BaseModel):
    friend_username: str = Field(...)

class AcceptFriendSchema(BaseModel):
    request_id: int = Field(...)

class DeleteFriendSchema(BaseModel):
    friend_username: str = Field(...)

# A. 发起好友申请
@router.post("/add-friend")
async def add_friend(data: AddFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    friend = data.friend_username.strip()

    if username == friend:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE username = %s", (friend,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="该用户不存在")

        cur.execute("""
            SELECT id, status, username FROM friendships 
            WHERE (username = %s AND friend_username = %s) OR (username = %s AND friend_username = %s)
        """, (username, friend, friend, username))
        row = cur.fetchone()
        
        if row:
            status_val = row[1]
            requester = row[2]
            if status_val == 'accepted':
                raise HTTPException(status_code=400, detail="你们已经是好友了")
            else:
                if requester == username:
                    raise HTTPException(status_code=400, detail="好友申请已发送，等待对方审核")
                else:
                    raise HTTPException(status_code=400, detail="对方已向你发送好友申请，请前往通知页面同意")

        cur.execute("INSERT INTO friendships (username, friend_username, status) VALUES (%s, %s, 'pending')", (username, friend))
        conn.commit()
        return {"success": True, "message": "好友申请已发送，等待对方审核"}
    finally:
        cur.close()
        conn.close()

# B. 获取待我审批的好友申请
@router.get("/friend-requests/pending")
async def get_pending_requests(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT f.id, f.username, COALESCE(u.nickname, f.username), COALESCE(u.avatar_url, '👤')
            FROM friendships f
            JOIN users u ON f.username = u.username
            WHERE f.friend_username = %s AND f.status = 'pending'
        """, (username,))
        records = cur.fetchall()
        requests = [{"id": r[0], "username": r[1], "nickname": r[2], "avatar": r[3]} for r in records]
        return {"success": True, "requests": requests}
    finally:
        cur.close()
        conn.close()

# C. 同意好友申请
@router.post("/friend-requests/accept")
async def accept_friend_request(data: AcceptFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT friend_username FROM friendships WHERE id = %s", (data.request_id,))
        row = cur.fetchone()
        if not row or row[0] != username:
            raise HTTPException(status_code=403, detail="无权处理该好友请求")
            
        cur.execute("UPDATE friendships SET status = 'accepted' WHERE id = %s", (data.request_id,))
        conn.commit()
        return {"success": True, "message": "已同意好友请求，你们现在是好友了"}
    finally:
        cur.close()
        conn.close()

# D. 拒绝/删除好友申请
@router.post("/friend-requests/reject")
async def reject_friend_request(data: AcceptFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT friend_username FROM friendships WHERE id = %s", (data.request_id,))
        row = cur.fetchone()
        if not row or row[0] != username:
            raise HTTPException(status_code=403, detail="无权处理该好友请求")
            
        cur.execute("DELETE FROM friendships WHERE id = %s", (data.request_id,))
        conn.commit()
        return {"success": True, "message": "已拒绝好友请求"}
    finally:
        cur.close()
        conn.close()

# E. 解除好友关系 (保留历史聊天记录)
@router.post("/friend/delete")
async def delete_friend(data: DeleteFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    friend = data.friend_username.strip()

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM friendships 
            WHERE (username = %s AND friend_username = %s) OR (username = %s AND friend_username = %s)
        """, (username, friend, friend, username))
        conn.commit()
        return {"success": True, "message": f"已成功与 @{friend} 解除好友关系（历史聊天记录已为您保留）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解除好友异常: {e}")
    finally:
        cur.close()
        conn.close()

# F. 获取我已同意的好友列表 (💡 支持 R2 云端图片在最新消息中识别为 [图片])
@router.get("/friends")
async def get_friends(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT CASE 
                WHEN f.username = %s THEN f.friend_username 
                ELSE f.username 
            END as friend,
            COALESCE(u.nickname, CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END),
            COALESCE(u.avatar_url, '👤')
            FROM friendships f
            JOIN users u ON u.username = CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END
            WHERE (f.username = %s OR f.friend_username = %s) AND f.status = 'accepted'
        """, (username, username, username, username, username))
        records = cur.fetchall()
        
        friends = []
        for row in records:
            friend_username = row[0]
            friend_nickname = row[1]
            friend_avatar = row[2]
            
            # 统计未读
            cur.execute("""
                SELECT COUNT(*) 
                FROM chat_messages 
                WHERE sender = %s AND receiver = %s AND is_read = FALSE
            """, (friend_username, username))
            unread_count = cur.fetchone()[0]
            
            # 查询最新一条消息
            cur.execute("""
                SELECT message, sender, created_at, is_recalled 
                FROM chat_messages 
                WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
                ORDER BY created_at DESC 
                LIMIT 1
            """, (username, friend_username, friend_username, username))
            msg_row = cur.fetchone()
            
            last_msg = ""
            last_msg_time = ""
            if msg_row:
                raw_msg = msg_row[0]
                sender = msg_row[1]
                created_at = msg_row[2] + timedelta(hours=8)
                is_recalled = msg_row[3]
                
                # 如果已被逻辑撤回，摘要直接显示撤回语
                if is_recalled:
                    display_msg = "你撤回了一条消息" if sender == username else "对方撤回了一条消息"
                    last_msg = display_msg
                else:
                    # 💡 核心修改：不仅检测 data:image/ 前缀，同时检测是否以常见图片后缀结尾（适配 R2 远程 URL）
                    is_img = raw_msg.startswith("data:image/") or any(raw_msg.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"])
                    if is_img:
                        display_msg = "[图片]"
                    else:
                        display_msg = raw_msg[:15] + "..." if len(raw_msg) > 15 else raw_msg
                    
                    prefix = "我" if sender == username else friend_nickname
                    last_msg = f"{prefix}: {display_msg}"
                
                last_msg_time = created_at.strftime("%H:%M")
            
            friends.append({
                "username": friend_username,
                "nickname": friend_nickname,
                "avatar": friend_avatar,
                "last_message": last_msg,
                "last_message_time": last_msg_time,
                "unread": unread_count
            })
        return {"success": True, "friends": friends}
    finally:
        cur.close()
        conn.close()

# G. 获取历史消息 (💡 支持 is_recalled 逻辑删除字段渲染)
@router.get("/history/{friend_username}")
async def get_chat_history(friend_username: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 打开窗口自动更新未读数
        cur.execute("""
            UPDATE chat_messages 
            SET is_read = TRUE 
            WHERE sender = %s AND receiver = %s AND is_read = FALSE
        """, (friend_username, username))
        conn.commit()

        cur.execute("""
            SELECT id, sender, receiver, message, is_read, is_recalled, created_at 
            FROM chat_messages 
            WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
            ORDER BY created_at ASC
        """, (username, friend_username, friend_username, username))
        records = cur.fetchall()
        
        history = []
        for row in records:
            beijing_time = row[6] + timedelta(hours=8)
            is_recalled = row[5]
            
            # 💡 核心修改：如果数据库中被标记为逻辑撤回（is_recalled = True）
            # 则不输出真实内容，而是将文本替换为对应的撤回声明，并加上 system=True 气泡标记
            display_text = row[3]
            is_system = False
            if is_recalled:
                is_system = True
                display_text = "你撤回了一条消息" if row[1] == username else "对方撤回了一条消息"

            history.append({
                "id": row[0],
                "from": row[1],
                "to": row[2],
                "text": display_text,
                "is_read": row[4], 
                "time": beijing_time.strftime("%m-%d %H:%M"),
                "self": row[1] == username,
                "system": is_system
            })
        return {"success": True, "history": history}
    finally:
        cur.close()
        conn.close()

# H. Cloudflare R2 图片直传接口
@router.post("/upload")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="只允许上传图片格式文件 (png, jpg, jpeg, gif, webp)")

    if not r2_client or not R2_BUCKET_NAME or not R2_PUBLIC_URL:
        raise HTTPException(status_code=500, detail="服务器未正确配置 Cloudflare R2 存储环境变量")

    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    content_type_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp"
    }
    mime_type = content_type_map.get(file_extension, "application/octet-stream")

    try:
        await file.seek(0)
        file_bytes = await file.read()
        r2_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=unique_filename,
            Body=file_bytes,
            ContentType=mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传至 Cloudflare R2 失败: {e}")
    finally:
        file.file.close()

    public_image_url = f"{R2_PUBLIC_URL.rstrip('/')}/{unique_filename}"
    return {"success": True, "url": public_image_url}


# WebSocket 实时常驻分发器 (逻辑删除与分发)
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]

    async def send_direct_message(self, message: str, sender: str, receiver: str):
        conn = get_db_connection()
        cur = conn.cursor()
        message_id = None
        try:
            cur.execute(
                "INSERT INTO chat_messages (sender, receiver, message) VALUES (%s, %s, %s) RETURNING id",
                (sender, receiver, message)
            )
            message_id = cur.fetchone()[0]
            conn.commit()
        except Exception as e:
            print(f"💾 写入消息历史失败: {e}")
        finally:
            cur.close()
            conn.close()

        if receiver in self.active_connections:
            await self.active_connections[receiver].send_json({
                "type": "msg",
                "id": message_id,
                "from": sender,
                "message": message
            })

manager = ConnectionManager()

@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "msg")  
            target_user = data.get("to")
            
            # 情况 A：标准消息
            if msg_type == "msg":
                msg = data.get("message")
                if target_user and msg:
                    await manager.send_direct_message(msg, username, target_user)
            
            # 情况 B：已读回执
            elif msg_type == "read":
                if target_user:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE chat_messages 
                        SET is_read = TRUE 
                        WHERE sender = %s AND receiver = %s AND is_read = FALSE
                    """, (target_user, username))
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    if target_user in manager.active_connections:
                        await manager.active_connections[target_user].send_json({
                            "type": "read",
                            "from": username
                        })
            
            # 💡 情况 C：消息撤回 (升级为逻辑删除：UPDATE is_recalled = TRUE)
            elif msg_type == "recall":
                message_id = data.get("message_id")
                if message_id and target_user:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    try:
                        cur.execute(
                            "UPDATE chat_messages SET is_recalled = TRUE WHERE id = %s AND sender = %s",
                            (message_id, username)
                        )
                        conn.commit()
                    except Exception as e:
                        print(f"❌ 撤回消息失败: {e}")
                    finally:
                        cur.close()
                        conn.close()
                    
                    if target_user in manager.active_connections:
                        await manager.active_connections[target_user].send_json({
                            "type": "recall",
                            "from": username,
                            "message_id": message_id
                        })
                        
    except WebSocketDisconnect:
        manager.disconnect(username)