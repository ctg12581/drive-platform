# app/core/timeutil.py
"""时间序列化工具：统一把数据库时间输出为带时区的 UTC ISO 字符串。

前端只需 new Date(iso) 即可按设备本地时区正确展示，避免后端硬编码 +8 小时。
"""
from datetime import datetime, timezone


def to_iso_utc(value):
    """把 datetime 统一转换为带时区的 UTC ISO 字符串。

    - 若为 naive datetime，按 UTC 解释（数据库列已统一为 TIMESTAMPTZ，正常不会是 naive）。
    - 非 datetime（如 None）原样返回。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return value
