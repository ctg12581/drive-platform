# app/modules/chat/router.py
"""实时聊天、好友关系与图片上传模块。"""
import uuid
from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.db import db_cursor
from app.core.storage import r2_client
from app.modules.auth.service import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat 实时社交与好友关系"])

MUTUAL_FRIENDSHIP_WHERE = """
    (f.username = %s AND f.friend_username = %s)
    OR (f.username = %s AND f.friend_username = %s)
"""


class AddFriendSchema(BaseModel):
    friend_username: str = Field(...)


class AcceptFriendSchema(BaseModel):
    request_id: int = Field(...)


class DeleteFriendSchema(BaseModel):
    friend_username: str = Field(...)


@router.post("/add-friend")
async def add_friend(data: AddFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    friend = data.friend_username.strip()

    if username == friend:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE username = %s", (friend,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="该用户不存在")

        cur.execute(
            f"SELECT id, status, username FROM friendships f WHERE {MUTUAL_FRIENDSHIP_WHERE}",
            (username, friend, friend, username),
        )
        row = cur.fetchone()

        if row:
            status_val, requester = row[1], row[2]
            if status_val == "accepted":
                raise HTTPException(status_code=400, detail="你们已经是好友了")
            if requester == username:
                raise HTTPException(status_code=400, detail="好友申请已发送，等待对方审核")
            raise HTTPException(status_code=400, detail="对方已向你发送好友申请，请前往通知页面同意")

        cur.execute(
            "INSERT INTO friendships (username, friend_username, status) VALUES (%s, %s, 'pending')",
            (username, friend),
        )
    return {"success": True, "message": "好友申请已发送，等待对方审核"}


@router.get("/friend-requests/pending")
async def get_pending_requests(current_user: dict = Depends(get_current_user)):
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT f.id, f.username, COALESCE(u.nickname, f.username), COALESCE(u.avatar_url, '👤')
            FROM friendships f
            JOIN users u ON f.username = u.username
            WHERE f.friend_username = %s AND f.status = 'pending'
            """,
            (current_user["username"],),
        )
        records = cur.fetchall()
    return {
        "success": True,
        "requests": [
            {"id": r[0], "username": r[1], "nickname": r[2], "avatar": r[3]} for r in records
        ],
    }


@router.post("/friend-requests/accept")
async def accept_friend_request(data: AcceptFriendSchema, current_user: dict = Depends(get_current_user)):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT friend_username FROM friendships WHERE id = %s", (data.request_id,))
        row = cur.fetchone()
        if not row or row[0] != current_user["username"]:
            raise HTTPException(status_code=403, detail="无权处理该好友请求")
        cur.execute("UPDATE friendships SET status = 'accepted' WHERE id = %s", (data.request_id,))
    return {"success": True, "message": "已同意好友请求，你们现在是好友了"}


@router.post("/friend-requests/reject")
async def reject_friend_request(data: AcceptFriendSchema, current_user: dict = Depends(get_current_user)):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT friend_username FROM friendships WHERE id = %s", (data.request_id,))
        row = cur.fetchone()
        if not row or row[0] != current_user["username"]:
            raise HTTPException(status_code=403, detail="无权处理该好友请求")
        cur.execute("DELETE FROM friendships WHERE id = %s", (data.request_id,))
    return {"success": True, "message": "已拒绝好友请求"}


@router.post("/friend/delete")
async def delete_friend(data: DeleteFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    friend = data.friend_username.strip()
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(
                f"DELETE FROM friendships f WHERE {MUTUAL_FRIENDSHIP_WHERE}",
                (username, friend, friend, username),
            )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"解除好友异常: {exc}") from exc
    return {"success": True, "message": f"已成功与 @{friend} 解除好友关系（历史聊天记录已为您保留）"}


def summarize_last_message(raw_msg: str, sender: str, current_username: str, friend_nickname: str, is_recalled: bool) -> str:
    """生成好友列表中的最新消息摘要。"""
    if is_recalled:
        return "你撤回了一条消息" if sender == current_username else "对方撤回了一条消息"

    is_image = raw_msg.startswith("data:image/") or any(
        raw_msg.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    )
    if is_image:
        display_msg = "[图片]"
    else:
        display_msg = raw_msg[:15] + "..." if len(raw_msg) > 15 else raw_msg

    prefix = "我" if sender == current_username else friend_nickname
    return f"{prefix}: {display_msg}"


@router.get("/friends")
async def get_friends(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END AS friend,
                COALESCE(u.nickname, CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END),
                COALESCE(u.avatar_url, '👤')
            FROM friendships f
            JOIN users u ON u.username =
                CASE WHEN f.username = %s THEN f.friend_username ELSE f.username END
            WHERE (f.username = %s OR f.friend_username = %s) AND f.status = 'accepted'
            """,
            (username, username, username, username, username),
        )
        records = cur.fetchall()

        friends = []
        for friend_username, friend_nickname, friend_avatar in records:
            cur.execute(
                "SELECT COUNT(*) FROM chat_messages "
                "WHERE sender = %s AND receiver = %s AND is_read = FALSE",
                (friend_username, username),
            )
            unread_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT message, sender, created_at, is_recalled
                FROM chat_messages
                WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (username, friend_username, friend_username, username),
            )
            msg_row = cur.fetchone()

            last_msg = ""
            last_msg_time = ""
            if msg_row:
                raw_msg, sender, created_at, is_recalled = msg_row
                last_msg = summarize_last_message(raw_msg, sender, username, friend_nickname, is_recalled)
                last_msg_time = (created_at + timedelta(hours=8)).strftime("%H:%M")

            friends.append(
                {
                    "username": friend_username,
                    "nickname": friend_nickname,
                    "avatar": friend_avatar,
                    "last_message": last_msg,
                    "last_message_time": last_msg_time,
                    "unread": unread_count,
                }
            )
    return {"success": True, "friends": friends}


@router.get("/history/{friend_username}")
async def get_chat_history(friend_username: str, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    with db_cursor(commit=True) as cur:
        # 打开窗口即把对方发来的消息标记为已读
        cur.execute(
            "UPDATE chat_messages SET is_read = TRUE "
            "WHERE sender = %s AND receiver = %s AND is_read = FALSE",
            (friend_username, username),
        )

        cur.execute(
            """
            SELECT id, sender, receiver, message, is_read, is_recalled, created_at
            FROM chat_messages
            WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
            ORDER BY created_at ASC
            """,
            (username, friend_username, friend_username, username),
        )
        records = cur.fetchall()

    history = []
    for row in records:
        sender = row[1]
        is_recalled = row[5]
        display_text = row[3]
        is_system = False
        if is_recalled:
            is_system = True
            display_text = "你撤回了一条消息" if sender == username else "对方撤回了一条消息"

        history.append(
            {
                "id": row[0],
                "from": sender,
                "to": row[2],
                "text": display_text,
                "is_read": row[4],
                "time": (row[6] + timedelta(hours=8)).strftime("%m-%d %H:%M"),
                "self": sender == username,
                "system": is_system,
            }
        )
    return {"success": True, "history": history}


@router.post("/upload")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="只允许上传图片格式文件 (png, jpg, jpeg, gif, webp)")

    if not r2_client or not settings.R2_BUCKET_NAME or not settings.R2_PUBLIC_URL:
        raise HTTPException(status_code=500, detail="服务器未正确配置 Cloudflare R2 存储环境变量")

    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    content_type_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }

    try:
        await file.seek(0)
        file_bytes = await file.read()
        r2_client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=unique_filename,
            Body=file_bytes,
            ContentType=content_type_map.get(file_extension, "application/octet-stream"),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"上传至 Cloudflare R2 失败: {exc}") from exc
    finally:
        file.file.close()

    return {"success": True, "url": f"{settings.R2_PUBLIC_URL.rstrip('/')}/{unique_filename}"}


class ConnectionManager:
    """维护在线用户 -> WebSocket 的映射，并负责消息落库与转发。"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        self.active_connections.pop(username, None)

    async def send_direct_message(self, message: str, sender: str, receiver: str):
        message_id = None
        try:
            with db_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO chat_messages (sender, receiver, message) VALUES (%s, %s, %s) RETURNING id",
                    (sender, receiver, message),
                )
                message_id = cur.fetchone()[0]
        except Exception as exc:  # noqa: BLE001
            print(f"💾 写入消息历史失败: {exc}")

        target = self.active_connections.get(receiver)
        if target:
            await target.send_json(
                {"type": "msg", "id": message_id, "from": sender, "message": message}
            )


manager = ConnectionManager()


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "msg")
            target_user = data.get("to")

            if msg_type == "msg":
                msg = data.get("message")
                if target_user and msg:
                    await manager.send_direct_message(msg, username, target_user)

            elif msg_type == "read":
                if target_user:
                    with db_cursor(commit=True) as cur:
                        cur.execute(
                            "UPDATE chat_messages SET is_read = TRUE "
                            "WHERE sender = %s AND receiver = %s AND is_read = FALSE",
                            (target_user, username),
                        )
                    if target_user in manager.active_connections:
                        await manager.active_connections[target_user].send_json(
                            {"type": "read", "from": username}
                        )

            elif msg_type == "recall":
                message_id = data.get("message_id")
                if message_id and target_user:
                    with db_cursor(commit=True) as cur:
                        cur.execute(
                            "UPDATE chat_messages SET is_recalled = TRUE WHERE id = %s AND sender = %s",
                            (message_id, username),
                        )
                    if target_user in manager.active_connections:
                        await manager.active_connections[target_user].send_json(
                            {"type": "recall", "from": username, "message_id": message_id}
                        )
    except WebSocketDisconnect:
        manager.disconnect(username)
