# app/core/storage.py
"""Cloudflare R2 对象存储客户端。"""
from botocore.config import Config
import boto3

from app.core.config import settings


def create_r2_client():
    """按配置创建 S3 兼容的 R2 客户端；配置不全时返回 None。"""
    if not all(
        [
            settings.R2_ACCOUNT_ID,
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
        ]
    ):
        return None

    try:
        client = boto3.client(
            service_name="s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )
        print("✅ Cloudflare R2 存储客户端初始化成功")
        return client
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Cloudflare R2 存储客户端初始化失败: {exc}")
        return None


r2_client = create_r2_client()
