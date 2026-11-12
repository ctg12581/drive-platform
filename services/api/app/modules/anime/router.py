# app/modules/anime/router.py
# 动漫人物图鉴模块：作品表 anime_works + 角色表 anime_characters（角色通过 work_id 关联作品）。
# 数据由后台爬虫（AniList 日/国漫 + TVmaze 美漫）落库；本模块只读，公开访问、无需登录。
# 作品列表直接分页查询作品表（不做角色聚合）；角色数据在进入某部作品后再按 work_id 拉取。
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

CHARACTER_SELECT = (
    "SELECT c.id, c.external_id, c.name, c.name_en, c.avatar, c.image_url, c.tags, "
    "c.voice_actor, c.personality, c.introduction, c.quote, c.source, c.popularity, "
    "w.id AS work_id, w.title AS work_title, w.title_en AS work_title_en, w.region "
    "FROM anime_characters c JOIN anime_works w ON c.work_id = w.id"
)


def _decode_tags(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    return list(raw)


def _row_to_character(row) -> dict:
    """把作品+角色联表查询行转换为前端结构。"""
    return {
        "id": row["id"],
        "external_id": row["external_id"],
        "region": row["region"],
        "work_id": row["work_id"],
        "work": row["work_title"] or "",
        "work_en": row["work_title_en"] or "",
        "name": row["name"],
        "name_en": row["name_en"] or "",
        "avatar": row["avatar"] or "",
        "image_url": row["image_url"] or "",
        "tags": _decode_tags(row["tags"]),
        "voice_actor": row["voice_actor"] or "",
        "personality": row["personality"] or "",
        "introduction": row["introduction"] or "",
        "quote": row["quote"] or "",
        "source": row["source"] or "",
        "popularity": int(row["popularity"] or 0),
    }


def _serialize_detail(character: dict) -> dict:
    """详情：补充地区展示信息。"""
    meta = REGION_META.get(character["region"], {})
    return {
        **character,
        "region_name": meta.get("name", ""),
        "region_full": meta.get("full", ""),
        "region_emoji": meta.get("emoji", ""),
    }


def _match_keyword(character: dict, keyword: str) -> bool:
    """关键词匹配：人物名 / 作品名（中英文）+ 标签。"""
    fields = [
        character["name"],
        character["name_en"],
        character.get("work", ""),
        character.get("work_en", ""),
        *character.get("tags", []),
    ]
    return any(keyword in str(field).lower() for field in fields)


def _build_region_summary(pool: list) -> list:
    """按地区汇总角色数量。"""
    summary = [{"key": "all", "name": "全部", "full": "全部地区", "emoji": "🌏", "count": len(pool)}]
    for key in REGION_ORDER:
        summary.append({
            "key": key,
            **REGION_META[key],
            "count": sum(1 for c in pool if c["region"] == key),
        })
    return summary


async def _load_characters(work_id: int = 0, region: str = "", keyword: str = "") -> list[dict]:
    """按作品 / 地区读取角色（角色数据只在进入作品时查询）。"""
    clauses = []
    params: list = []
    if work_id:
        params.append(work_id)
        clauses.append(f"c.work_id = ${len(params)}")
    if region:
        params.append(region)
        clauses.append(f"w.region = ${len(params)}")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    try:
        async with db_conn() as conn:
            rows = await conn.fetch(
                f"{CHARACTER_SELECT}{where} ORDER BY c.popularity DESC, c.id ASC",
                *params,
            )
    except Exception as exc:  # noqa: BLE001 - 读库失败返回空
        print(f"⚠️ [ANIME] 读取角色失败: {exc}")
        return []

    characters = [_row_to_character(row) for row in rows]
    if keyword:
        kw = keyword.lower()
        characters = [c for c in characters if _match_keyword(c, kw)]
    return characters


# 1. 获取作品列表（分页；只查作品表，不返回角色）
@router.get("/works")
async def get_anime_works(
    keyword: str = Query("", description="按关键词过滤：作品名"),
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
        "WHERE ($1 = '' OR region = $1) "
        "AND ($2 = '' OR title ILIKE $3 OR title_en ILIKE $3)"
    )
    try:
        async with db_conn() as conn:
            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM anime_works {where}", region, keyword, kw_like
            )
            rows = await conn.fetch(
                f"""
                SELECT id, external_id, region, title, title_en, cover, tags, popularity, character_count
                FROM anime_works
                {where}
                ORDER BY popularity DESC, character_count DESC, id ASC
                LIMIT $4 OFFSET $5
                """,
                region, keyword, kw_like, page_size, offset,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [ANIME] 读取作品列表失败: {exc}")
        return {"success": True, "total": 0, "page": page, "page_size": page_size,
                "has_more": False, "works": []}

    works = []
    for row in rows:
        meta = REGION_META.get(row["region"], {})
        works.append({
            "id": row["id"],
            "work": row["title"],
            "work_en": row["title_en"] or "",
            "region": row["region"],
            "region_name": meta.get("name", ""),
            "region_full": meta.get("full", ""),
            "region_emoji": meta.get("emoji", ""),
            "count": int(row["character_count"] or 0),
            "cover": row["cover"] or "",
            "tags": _decode_tags(row["tags"]),
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


# 2. 获取角色列表（进入作品后按 work_id 拉取；也可按地区 / 关键词）
@router.get("/list")
async def get_anime_list(
    work_id: int = Query(0, ge=0, description="作品 id，进入某部作品时传入"),
    keyword: str = Query("", description="按关键词过滤：人物 / 标签（中英文均可）"),
    region: str = Query("", description="按地区过滤：jp 日本 / cn 中国 / us 美国，留空返回全部"),
):
    region = region.strip().lower()
    if region and region not in REGION_META:
        raise HTTPException(status_code=400, detail="不支持的地区筛选")

    matched = await _load_characters(work_id=work_id, region=region, keyword=keyword.strip())
    regions_summary = _build_region_summary(matched)

    characters = [
        {
            "id": c["id"],
            "region": c["region"],
            "work_id": c["work_id"],
            "work": c["work"],
            "work_en": c["work_en"],
            "name": c["name"],
            "name_en": c["name_en"],
            "avatar": c["avatar"],
            "image_url": c["image_url"],
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


# 3. 地区汇总（各地区角色数，供前端标签显示）
@router.get("/regions")
async def get_anime_regions():
    try:
        async with db_conn() as conn:
            rows = await conn.fetch(
                "SELECT w.region AS region, COUNT(c.id)::int AS cnt "
                "FROM anime_works w LEFT JOIN anime_characters c ON c.work_id = w.id "
                "GROUP BY w.region"
            )
        counts = {row["region"]: int(row["cnt"] or 0) for row in rows}
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [ANIME] 读取地区汇总失败: {exc}")
        counts = {}

    total = sum(counts.values())
    regions = [{"key": "all", "name": "全部", "full": "全部地区", "emoji": "🌏", "count": total}]
    for key in REGION_ORDER:
        regions.append({"key": key, **REGION_META[key], "count": counts.get(key, 0)})
    return {"success": True, "regions": regions}


# 4. 获取单个动漫人物详情
@router.get("/{character_id}")
async def get_anime_detail(character_id: int):
    try:
        async with db_conn() as conn:
            row = await conn.fetchrow(
                f"{CHARACTER_SELECT} WHERE c.id = $1", character_id
            )
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [ANIME] 读取角色详情失败: {exc}")
        row = None
    if row:
        return {"success": True, "character": _serialize_detail(_row_to_character(row))}
    raise HTTPException(status_code=404, detail="未找到该动漫人物")
