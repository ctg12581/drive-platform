# app/modules/anime/router.py
# 动漫人物图鉴模块：读取后台爬虫（AniList 日/国漫 + TVmaze 美漫）落库的快照 anime_characters，
# 提供列表（关键词 / 地区 / 作品筛选）、地区汇总、作品分类与详情只读接口，公开访问，无需登录鉴权。
# 表为空或数据库不可用时返回空结果（数据由定时爬虫负责填充），不再内置硬编码兜底数据。
import json

from fastapi import APIRouter, HTTPException, Query

from app.core.db import db_conn

router = APIRouter(prefix="/anime", tags=["Anime 动漫人物图鉴"])

# 地区元数据：key 用于接口过滤，name 为图鉴短标签，full 为地区全称
REGION_META = {
    "jp": {"name": "日漫", "full": "日本", "emoji": "🇯🇵"},
    "cn": {"name": "国漫", "full": "中国", "emoji": "🇨🇳"},
    "us": {"name": "美漫", "full": "美国", "emoji": "🇺🇸"},
}
REGION_ORDER = ["jp", "cn", "us"]


def _match_keyword(character: dict, keyword: str) -> bool:
    """关键词匹配：人物名 / 作品名（中英文）+ 标签，全部忽略大小写。"""
    fields = [
        character["name"],
        character["name_en"],
        character["work"],
        character["work_en"],
        *character.get("tags", []),
    ]
    return any(keyword in str(field).lower() for field in fields)


def _build_region_summary(pool: list) -> list:
    """按地区汇总数量，pool 为已按关键词过滤（但未按地区过滤）的角色集合。"""
    summary = [{"key": "all", "name": "全部", "full": "全部地区", "emoji": "🌏", "count": len(pool)}]
    for key in REGION_ORDER:
        summary.append({
            "key": key,
            **REGION_META[key],
            "count": sum(1 for c in pool if c["region"] == key),
        })
    return summary


def _serialize_detail(character: dict) -> dict:
    """详情：在原始字段上补充地区展示信息。"""
    meta = REGION_META.get(character["region"], {})
    return {
        **character,
        "region_name": meta.get("name", ""),
        "region_full": meta.get("full", ""),
        "region_emoji": meta.get("emoji", ""),
    }


def _row_to_character(row) -> dict:
    """把 anime_characters 查询行转换为前端结构。"""
    tags = row["tags"] or []
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = []
    return {
        "id": row["id"],
        "external_id": row["external_id"],
        "region": row["region"],
        "name": row["name"],
        "name_en": row["name_en"] or "",
        "work": row["work"] or "",
        "work_en": row["work_en"] or "",
        "avatar": row["avatar"] or "",
        "image_url": row["image_url"] or "",
        "tags": list(tags),
        "voice_actor": row["voice_actor"] or "",
        "personality": row["personality"] or "",
        "introduction": row["introduction"] or "",
        "quote": row["quote"] or "",
        "source": row["source"] or "",
        "popularity": int(row["popularity"] or 0),
    }


async def _load_characters() -> list[dict]:
    """读取爬虫落库的角色快照；表为空或读库异常时返回空列表（由定时爬虫负责填充）。"""
    try:
        async with db_conn() as conn:
            rows = await conn.fetch(
                "SELECT id, external_id, region, name, name_en, work, work_en, avatar, image_url, "
                "tags, voice_actor, personality, introduction, quote, source, popularity "
                "FROM anime_characters ORDER BY popularity DESC, id ASC"
            )
        return [_row_to_character(row) for row in rows]
    except Exception as exc:  # noqa: BLE001 - 读库失败返回空列表，不阻断接口
        print(f"⚠️ [ANIME] 读取数据库失败: {exc}")
        return []


# 1. 获取动漫人物列表（支持关键词 name / work 与地区 region / 作品 work 过滤）
@router.get("/list")
async def get_anime_list(
    keyword: str = Query("", description="按关键词过滤：人物 / 作品 / 标签（中英文均可）"),
    region: str = Query("", description="按地区过滤：jp 日本 / cn 中国 / us 美国，留空返回全部"),
    work: str = Query("", description="按动漫作品名精确过滤，留空返回全部"),
):
    keyword = keyword.strip().lower()
    region = region.strip().lower()
    work = work.strip()
    if region and region not in REGION_META:
        raise HTTPException(status_code=400, detail="不支持的地区筛选")

    matched = await _load_characters()
    if keyword:
        matched = [c for c in matched if _match_keyword(c, keyword)]

    # 地区计数基于关键词过滤结果（不含地区过滤），保证切换标签时数字稳定
    regions_summary = _build_region_summary(matched)

    if region:
        matched = [c for c in matched if c["region"] == region]
    if work:
        matched = [c for c in matched if c["work"] == work]

    # 列表返回精简字段，避免一次性传输过长介绍
    characters = [
        {
            "id": c["id"],
            "name": c["name"],
            "name_en": c["name_en"],
            "work": c["work"],
            "work_en": c["work_en"],
            "region": c["region"],
            "avatar": c["avatar"],
            "image_url": c.get("image_url", ""),
            "tags": c["tags"],
        }
        for c in matched
    ]
    return {
        "success": True,
        "total": len(characters),
        "regions": regions_summary,
        "characters": characters,
    }


# 2. 获取地区汇总（供前端初始化筛选项，独立于关键词/地区过滤）
@router.get("/regions")
async def get_anime_regions():
    return {"success": True, "regions": _build_region_summary(await _load_characters())}


# 3. 按动漫作品分页（只返回作品聚合，不返回角色；进入作品后再调 /list 取角色）
@router.get("/works")
async def get_anime_works(
    keyword: str = Query("", description="按关键词过滤：作品 / 人物 / 标签"),
    region: str = Query("", description="按地区过滤：jp 日本 / cn 中国 / us 美国，留空返回全部"),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(30, ge=1, le=100, description="每页作品数"),
):
    keyword = keyword.strip()
    region = region.strip().lower()
    if region and region not in REGION_META:
        raise HTTPException(status_code=400, detail="不支持的地区筛选")

    offset = (page - 1) * page_size
    kw_like = f"%{keyword}%"
    where = (
        "WHERE ($1 = '' OR region = $1) AND ("
        "$2 = '' OR work ILIKE $3 OR work_en ILIKE $3 OR name ILIKE $3 OR name_en ILIKE $3 "
        "OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(tags) AS tg WHERE tg ILIKE $3)"
        ")"
    )

    try:
        async with db_conn() as conn:
            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM (SELECT 1 FROM anime_characters {where} GROUP BY region, work) AS t",
                region, keyword, kw_like,
            )
            rows = await conn.fetch(
                f"""
                SELECT region, work,
                       MAX(work_en) AS work_en,
                       COUNT(*)::int AS cnt,
                       MAX(popularity)::int AS popularity,
                       (ARRAY_AGG(image_url ORDER BY popularity DESC)
                            FILTER (WHERE image_url <> ''))[1] AS cover
                FROM anime_characters
                {where}
                GROUP BY region, work
                ORDER BY popularity DESC, cnt DESC, work ASC
                LIMIT $4 OFFSET $5
                """,
                region, keyword, kw_like, page_size, offset,
            )
    except Exception as exc:  # noqa: BLE001 - 读库失败返回空页
        print(f"⚠️ [ANIME] 读取作品列表失败: {exc}")
        return {"success": True, "total": 0, "page": page, "page_size": page_size,
                "has_more": False, "works": []}

    works = []
    for row in rows:
        meta = REGION_META.get(row["region"], {})
        works.append({
            "work": row["work"],
            "work_en": row["work_en"] or "",
            "region": row["region"],
            "region_name": meta.get("name", ""),
            "region_full": meta.get("full", ""),
            "region_emoji": meta.get("emoji", ""),
            "count": int(row["cnt"] or 0),
            "cover": row["cover"] or "",
            "popularity": int(row["popularity"] or 0),
        })

    total = int(total or 0)
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": offset + len(works) < total,
        "works": works,
    }


# 4. 获取单个动漫人物详情
@router.get("/{character_id}")
async def get_anime_detail(character_id: int):
    for c in await _load_characters():
        if c["id"] == character_id:
            return {"success": True, "character": _serialize_detail(c)}
    raise HTTPException(status_code=404, detail="未找到该动漫人物")
