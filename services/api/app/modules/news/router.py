# app/modules/news/router.py
# 热点新闻模块：为主页「热点 / 榜单」两个标签页提供数据。
#
# 数据来源：只读 crawler 定时抓取并落库的真实快照（hot_news 表）。
# 不再返回任何内置示例数据——避免出现「内容和原站对不上」的问题。
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import settings
from app.core.db import db_conn
from app.core.timeutil import to_iso_utc
from app.modules.admin.router import get_current_admin
from app.modules.news.crawler import crawl_all, trigger_background_crawl

router = APIRouter(prefix="/news", tags=["News 热点新闻"])

# 国内来源白名单（其余来源视为国外/海外来源），用于「国内 / 国外」分区
DOMESTIC_SOURCES = ["微博热搜", "知乎热榜", "百度热搜", "今日头条", "36氪"]


def serialize_db_row(row) -> dict:
    """把 hot_news 查询行序列化为前端结构。"""
    return {
        "id": row[0],
        "source": row[1],
        "category": row[2],
        "title": row[3],
        "summary": row[4] or "",
        "url": row[5] or "",
        "hot": int(row[6] or 0),
        "image": row[7] or "",
        "published_at": to_iso_utc(row[8]),
    }


@router.get("/hot")
async def get_hot_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: str = Query("", description="按分类过滤，留空返回全部"),
    kind: str = Query("", description="按板块过滤：news 热点 / rank 榜单，留空返回全部"),
    region: str = Query("", description="按地区过滤：cn 国内 / intl 国外，留空返回全部"),
):
    """热点/榜单列表（分页）：读定时抓取的真实快照；无数据时返回空并触发后台补抓。

    region=cn 只返回国内来源，region=intl 只返回国外来源（按抓取来源划分）。
    """
    category = category.strip()
    kind = kind.strip()
    region = region.strip().lower()
    offset = (page - 1) * page_size

    params: list = [category, kind]
    region_clause = ""
    if region in ("cn", "intl"):
        params.append(DOMESTIC_SOURCES)
        idx = len(params)
        if region == "cn":
            # 国内：国内来源，且分类不是「国际」
            region_clause = f"AND source = ANY(${idx}::text[]) AND category <> '国际'"
        else:
            # 国外：海外来源，或任何来源下的「国际」类内容
            region_clause = f"AND (NOT (source = ANY(${idx}::text[])) OR category = '国际')"

    try:
        async with db_conn() as conn:
            meta = await conn.fetchrow(
                f"""
                SELECT COUNT(*) AS total, MAX(fetched_at) AS updated
                FROM hot_news
                WHERE fetched_at > now() - interval '24 hours'
                  AND ($1 = '' OR category = $1)
                  AND ($2 = '' OR kind = $2)
                  {region_clause}
                """,
                *params,
            )
            total = int(meta["total"] or 0) if meta else 0
            if total > 0:
                limit_idx, offset_idx = len(params) + 1, len(params) + 2
                records = await conn.fetch(
                    f"""
                    SELECT id, source, category, title, summary, url, hot, image_url, fetched_at
                    FROM (
                        SELECT id, source, category, title, summary, url, hot, image_url, fetched_at,
                               ROW_NUMBER() OVER (PARTITION BY source ORDER BY hot DESC, id ASC) AS rn
                        FROM hot_news
                        WHERE fetched_at > now() - interval '24 hours'
                          AND ($1 = '' OR category = $1)
                          AND ($2 = '' OR kind = $2)
                          {region_clause}
                    ) t
                    ORDER BY rn ASC, hot DESC, id ASC
                    LIMIT ${limit_idx} OFFSET ${offset_idx}
                    """,
                    *params,
                    page_size,
                    offset,
                )
                updated = (meta["updated"] if meta else None) or datetime.now(timezone.utc)
                # 快照过期（如 Render 免费实例休眠后重启）时，非阻塞地在后台补抓
                if datetime.now(timezone.utc) - updated > timedelta(
                    minutes=max(1, settings.NEWS_CRAWL_INTERVAL_MINUTES)
                ):
                    trigger_background_crawl()
                return {
                    "success": True,
                    "source": "crawl",
                    "updated_at": to_iso_utc(updated),
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "has_more": offset + len(records) < total,
                    "news": [serialize_db_row(r) for r in records],
                }
    except Exception as exc:  # noqa: BLE001 - 读库异常不应影响接口可用性
        print(f"⚠️ [NEWS] 读取热点库失败: {exc}")

    # 库内无数据：后台补抓一次，本次返回空列表（绝不用内置示例冒充真实热榜）
    trigger_background_crawl()
    return {
        "success": True,
        "source": "empty",
        "updated_at": None,
        "total": 0,
        "page": page,
        "page_size": page_size,
        "has_more": False,
        "news": [],
    }


@router.get("/categories")
async def get_news_categories():
    """返回当前快照里实际出现的分类。"""
    try:
        async with db_conn() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM hot_news "
                "WHERE fetched_at > now() - interval '24 hours' AND category <> '' "
                "ORDER BY category"
            )
        return {"success": True, "categories": [r[0] for r in rows]}
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [NEWS] 读取热点分类失败: {exc}")
        return {"success": True, "categories": []}


@router.post("/crawl")
async def trigger_crawl(_: dict = Depends(get_current_admin)):
    """手动触发一次热点抓取（仅管理员）。"""
    count = await crawl_all()
    return {"success": True, "count": count, "message": f"本轮已抓取 {count} 条热点"}


@router.get("/{news_id}")
async def get_news_detail(news_id: int):
    """按 id 返回库内单条热点。"""
    try:
        async with db_conn() as conn:
            row = await conn.fetchrow(
                "SELECT id, source, category, title, summary, url, hot, image_url, fetched_at "
                "FROM hot_news WHERE id = $1",
                news_id,
            )
        if row:
            return {"success": True, "news": serialize_db_row(row)}
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [NEWS] 读取热点详情失败: {exc}")
    raise HTTPException(status_code=404, detail="未找到该热点新闻")
