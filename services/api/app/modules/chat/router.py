# app/modules/chat/router.py
"""实时聊天、好友关系与图片上传模块（asyncpg 全异步）。"""
import uuid
from typing import Dict, Set

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.db import db_conn, db_transaction
from app.core.storage import r2_client
from app.core.timeutil import to_iso_utc
from app.modules.auth.service import decode_token, get_current_user

router = APIRouter(prefix="/chat", tags=["Chat 实时社交与好友关系"])

IMAGE_CONTENT_TYPES = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


class AddFriendSchema(BaseModel):
    friend_username: str = Field(...)


class AcceptFriendSchema(BaseModel):
    request_id: int = Field(...)


class DeleteFriendSchema(BaseModel):
    friend_username: str = Field(...)


async def _are_friends(conn, username: str, friend: str) -> bool:
    row = await conn.fetchval(
        "SELECT 1 FROM friendships "
        "WHERE status = 'accepted' AND "
        "((username = $1 AND friend_username = $2) OR (username = $3 AND friend_username = $4))",
        username,
        friend,
        friend,
        username,
    )
    return row is not None


@router.post("/add-friend")
async def add_friend(data: AddFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    friend = data.friend_username.strip()

    if username == friend:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    async with db_transaction() as conn:
        exists = await conn.fetchval("SELECT id FROM users WHERE username = $1", friend)
        if not exists:
            raise HTTPException(status_code=404, detail="该用户不存在")

        row = await conn.fetchrow(
            "SELECT id, status, username FROM friendships f WHERE "
            "(f.username = $1 AND f.friend_username = $2) OR (f.username = $3 AND f.friend_username = $4)",
            username,
            friend,
            friend,
            username,
        )

        if row:
            status_val, requester = row["status"], row["username"]
            if status_val == "accepted":
                raise HTTPException(status_code=400, detail="你们已经是好友了")
            if requester == username:
                raise HTTPException(status_code=400, detail="好友申请已发送，等待对方审核")
            raise HTTPException(status_code=400, detail="对方已向你发送好友申请，请前往通知页面同意")

        await conn.execute(
            "INSERT INTO friendships (username, friend_username, status) VALUES ($1, $2, 'pending')",
            username,
            friend,
        )
    return {"success": True, "message": "好友申请已发送，等待对方审核"}


@router.get("/friend-requests/pending")
async def get_pending_requests(current_user: dict = Depends(get_current_user)):
    async with db_conn() as conn:
        records = await conn.fetch(
            """
            SELECT f.id, f.username, COALESCE(u.nickname, f.username), COALESCE(u.avatar_url, '👤')
            FROM friendships f
            JOIN users u ON f.username = u.username
            WHERE f.friend_username = $1 AND f.status = 'pending'
            """,
            current_user["username"],
        )
    return {
        "success": True,
        "requests": [
            {"id": r[0], "username": r[1], "nickname": r[2], "avatar": r[3]} for r in records
        ],
    }


@router.post("/friend-requests/accept")
async def accept_friend_request(data: AcceptFriendSchema, current_user: dict = Depends(get_current_user)):
    async with db_transaction() as conn:
        row = await conn.fetchrow(
            "SELECT friend_username FROM friendships WHERE id = $1", data.request_id
        )
        if not row or row[0] != current_user["username"]:
            raise HTTPException(status_code=403, detail="无权处理该好友请求")
        await conn.execute(
            "UPDATE friendships SET status = 'accepted' WHERE id = $1", data.request_id
        )
    return {"success": True, "message": "已同意好友请求，你们现在是好友了"}


@router.post("/friend-requests/reject")
async def reject_friend_request(data: AcceptFriendSchema, current_user: dict = Depends(get_current_user)):
    async with db_transaction() as conn:
        row = await conn.fetchrow(
            "SELECT friend_username FROM friendships WHERE id = $1", data.request_id
        )
        if not row or row[0] != current_user["username"]:
            raise HTTPException(status_code=403, detail="无权处理该好友请求")
        await conn.execute("DELETE FROM friendships WHERE id = $1", data.request_id)
    return {"success": True, "message": "已拒绝好友请求"}


@router.post("/friend/delete")
async def delete_friend(data: DeleteFriendSchema, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    friend = data.friend_username.strip()
    try:
        async with db_transaction() as conn:
            await conn.execute(
                "DELETE FROM friendships WHERE "
                "(username = $1 AND friend_username = $2) OR (username = $3 AND friend_username = $4)",
                username,
                friend,
                friend,
                username,
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
    """好友列表：固定 3 次查询完成，避免逐个好友的 N+1 查询。"""
    username = current_user["username"]
    async with db_conn() as conn:
        friend_rows = await conn.fetch(
            """
            SELECT DISTINCT
                CASE WHEN f.username = $1 THEN f.friend_username ELSE f.username END AS friend,
                COALESCE(u.nickname, CASE WHEN f.username = $2 THEN f.friend_username ELSE f.username END),
                COALESCE(u.avatar_url, '👤')
            FROM friendships f
            JOIN users u ON u.username =
                CASE WHEN f.username = $3 THEN f.friend_username ELSE f.username END
            WHERE (f.username = $4 OR f.friend_username = $5) AND f.status = 'accepted'
            """,
            username,
            username,
            username,
            username,
            username,
        )

        unread_rows = await conn.fetch(
            "SELECT sender, COUNT(*) FROM chat_messages "
            "WHERE receiver = $1 AND is_read = FALSE GROUP BY sender",
            username,
        )
        unread_map = {row[0]: row[1] for row in unread_rows}

        last_rows = await conn.fetch(
            """
            SELECT DISTINCT ON (other) other, message, sender, created_at, is_recalled
            FROM (
                SELECT CASE WHEN sender = $1 THEN receiver ELSE sender END AS other,
                       message, sender, created_at, is_recalled
                FROM chat_messages
                WHERE sender = $2 OR receiver = $3
            ) t
            ORDER BY other, created_at DESC
            """,
            username,
            username,
            username,
        )
        last_msg_map = {row[0]: row for row in last_rows}

    friends = []
    for friend_username, friend_nickname, friend_avatar in friend_rows:
        msg_row = last_msg_map.get(friend_username)
        last_msg = ""
        last_msg_time = None
        if msg_row:
            _, raw_msg, sender, created_at, is_recalled = msg_row
            last_msg = summarize_last_message(raw_msg, sender, username, friend_nickname, is_recalled)
            last_msg_time = to_iso_utc(created_at)

        friends.append(
            {
                "username": friend_username,
                "nickname": friend_nickname,
                "avatar": friend_avatar,
                "last_message": last_msg,
                "last_message_time": last_msg_time,
                "unread": unread_map.get(friend_username, 0),
            }
        )
    return {"success": True, "friends": friends}


@router.get("/history/{friend_username}")
async def get_chat_history(
    friend_username: str,
    limit: int = Query(200, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    username = current_user["username"]
    async with db_transaction() as conn:
        # 只有存在未读时才写库，避免每次打开会话都产生无用 UPDATE
        has_unread = await conn.fetchval(
            "SELECT 1 FROM chat_messages WHERE sender = $1 AND receiver = $2 "
            "AND is_read = FALSE LIMIT 1",
            friend_username,
            username,
        )
        if has_unread:
            await conn.execute(
                "UPDATE chat_messages SET is_read = TRUE "
                "WHERE sender = $1 AND receiver = $2 AND is_read = FALSE",
                friend_username,
                username,
            )

        # UNION ALL 让两个方向分别命中 (sender, receiver) 索引；只取最近 limit 条
        records = await conn.fetch(
            """
            SELECT * FROM (
                SELECT id, sender, receiver, message, is_read, is_recalled, created_at
                FROM chat_messages WHERE sender = $1 AND receiver = $2
                UNION ALL
                SELECT id, sender, receiver, message, is_read, is_recalled, created_at
                FROM chat_messages WHERE sender = $3 AND receiver = $4
            ) t
            ORDER BY created_at DESC
            LIMIT $5
            """,
            username,
            friend_username,
            friend_username,
            username,
            limit,
        )
        records = list(reversed(records))

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
                "time": to_iso_utc(row[6]),
                "self": sender == username,
                "system": is_system,
            }
        )
    return {"success": True, "history": history}


def _detect_image_extension(data: bytes) -> str | None:
    """基于文件头魔数识别图片类型，避免仅靠扩展名信任客户端。"""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "gif"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


@router.post("/upload")
async def upload_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not r2_client or not settings.R2_BUCKET_NAME or not settings.R2_PUBLIC_URL:
        raise HTTPException(status_code=500, detail="服务器未正确配置 Cloudflare R2 存储环境变量")

    try:
        stream = file.file
        # 先探测大小与文件头，再流式上传，避免把整张图读进内存
        stream.seek(0, 2)
        size = stream.tell()
        stream.seek(0)
        if size == 0:
            raise HTTPException(status_code=400, detail="上传文件为空")
        if size > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"图片过大，限制小于 {settings.MAX_UPLOAD_BYTES // (1024 * 1024)}MB",
            )

        file_extension = _detect_image_extension(stream.read(16))
        if file_extension is None:
            raise HTTPException(status_code=400, detail="文件内容不是有效图片（支持 png/jpg/gif/webp）")
        stream.seek(0)

        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        # boto3 是同步库，放到线程池执行，避免阻塞事件循环
        await run_in_threadpool(
            r2_client.upload_fileobj,
            stream,
            settings.R2_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": IMAGE_CONTENT_TYPES.get(file_extension, "application/octet-stream")},
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"上传至 Cloudflare R2 失败: {exc}") from exc
    finally:
        file.file.close()

    return {"success": True, "url": f"{settings.R2_PUBLIC_URL.rstrip('/')}/{unique_filename}"}


class ConnectionManager:
    """维护在线用户 -> 多 WebSocket 集合的映射，并负责消息落库与转发。"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(username, set()).add(websocket)

    def disconnect(self, username: str, websocket: WebSocket):
        conns = self.active_connections.get(username)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self.active_connections.pop(username, None)

    async def send_to_user(self, username: str, payload: dict):
        for ws in list(self.active_connections.get(username, ())):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001 - 单个连接异常不影响其它连接
                pass

    async def send_direct_message(self, message: str, sender: str, receiver: str) -> int | None:
        """落库并转发给接收方；非好友或写入失败返回 None。"""
        try:
            async with db_transaction() as conn:
                if not await _are_friends(conn, sender, receiver):
                    return None
                message_id = await conn.fetchval(
                    "INSERT INTO chat_messages (sender, receiver, message) VALUES ($1, $2, $3) RETURNING id",
                    sender,
                    receiver,
                    message,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"💾 写入消息历史失败: {exc}")
            return None

        await self.send_to_user(
            receiver, {"type": "msg", "id": message_id, "from": sender, "message": message}
        )
        return message_id

    @staticmethod
    async def mark_read(owner: str, other: str):
        async with db_transaction() as conn:
            await conn.execute(
                "UPDATE chat_messages SET is_read = TRUE "
                "WHERE sender = $1 AND receiver = $2 AND is_read = FALSE",
                other,
                owner,
            )

    @staticmethod
    async def recall(message_id: int, sender: str):
        async with db_transaction() as conn:
            await conn.execute(
                "UPDATE chat_messages SET is_recalled = TRUE WHERE id = $1 AND sender = $2",
                message_id,
                sender,
            )


manager = ConnectionManager()


@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, token: str = ""):
    # 必须携带有效 Token 且与路径用户名一致，防止冒充任意用户
    if decode_token(token) != username:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(username, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "msg")
            target_user = data.get("to")

            if msg_type == "msg":
                msg = data.get("message")
                client_id = data.get("client_id")
                if target_user and msg:
                    message_id = await manager.send_direct_message(msg, username, target_user)
                    if message_id is None:
                        await websocket.send_json(
                            {"type": "error", "message": "消息发送失败：对方不是你的好友"}
                        )
                    else:
                        await websocket.send_json(
                            {"type": "msg_ack", "client_id": client_id, "id": message_id}
                        )

            elif msg_type == "read":
                if target_user:
                    await manager.mark_read(username, target_user)
                    await manager.send_to_user(target_user, {"type": "read", "from": username})

            elif msg_type == "recall":
                message_id = data.get("message_id")
                if message_id and target_user:
                    await manager.recall(message_id, username)
                    await manager.send_to_user(
                        target_user, {"type": "recall", "from": username, "message_id": message_id}
                    )
    except WebSocketDisconnect:
        manager.disconnect(username, websocket)
    except Exception as exc:  # noqa: BLE001
        print(f"🔌 WebSocket 异常断开: {exc}")
        manager.disconnect(username, websocket)
