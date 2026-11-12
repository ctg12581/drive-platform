# app/modules/news/router.py
# 热点新闻模块：为主页「推荐」流提供热点新闻榜单。
#
# 数据来源：优先读取 crawler 定时抓取并落库的最新快照（hot_news 表）；
# 若数据库暂无数据（例如首次启动尚未抓取、或外网不可达），自动回退到内置榜单，保证前端不为空。
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import settings
from app.core.db import db_conn
from app.core.timeutil import to_iso_utc
from app.modules.admin.router import get_current_admin
from app.modules.news.crawler import crawl_all, trigger_background_crawl

router = APIRouter(prefix="/news", tags=["News 热点新闻"])

# 每条热点字段：
#   id            唯一标识
#   title         标题
#   summary       摘要（详情弹窗展示）
#   source        来源榜单
#   category      分类
#   hot           热度值（用于排序与展示）
#   url           原文 / 榜单链接
#   age_minutes   距今分钟数（每次请求动态换算为"刚发布"的相对时间，保证观感新鲜）
HOT_NEWS = [
    {
        "id": 1,
        "title": "国产大模型迎来新一轮能力升级，多模态应用加速落地",
        "summary": "多家厂商集中发布新一代大模型，在长文本理解、图像与音视频生成等方向持续突破，"
        "办公、教育、医疗等场景的落地案例明显增多。",
        "source": "微博热搜",
        "category": "科技",
        "hot": 986000,
        "url": "https://s.weibo.com/top/summary",
        "age_minutes": 12,
    },
    {
        "id": 2,
        "title": "新一代折叠屏手机集中发布，轻薄与续航成竞争焦点",
        "summary": "多款折叠屏新品在铰链工艺、机身厚度和电池续航上展开较量，价格区间进一步下探，"
        "引发消费者对高端换机的关注。",
        "source": "知乎热榜",
        "category": "科技",
        "hot": 732000,
        "url": "https://www.zhihu.com/hot",
        "age_minutes": 26,
    },
    {
        "id": 3,
        "title": "多部门出台举措提振消费，服务消费成增长新引擎",
        "summary": "围绕文旅、体育、养老等领域的一揽子促消费政策陆续落地，业内认为服务消费有望成为"
        "拉动内需的重要力量。",
        "source": "百度热搜",
        "category": "财经",
        "hot": 654000,
        "url": "https://top.baidu.com/board?tab=realtime",
        "age_minutes": 41,
    },
    {
        "id": 4,
        "title": "A股三大指数震荡整理，新能源板块表现活跃",
        "summary": "沪深两市成交保持活跃，光伏、储能等新能源方向盘中走强，机构提示关注中报业绩兑现情况。",
        "source": "今日头条",
        "category": "财经",
        "hot": 498000,
        "url": "https://www.toutiao.com/hot-event/hot-board/",
        "age_minutes": 58,
    },
    {
        "id": 5,
        "title": "全国田径锦标赛收官，多项赛会纪录被刷新",
        "summary": "本届赛事在短跑、跳远等项目上诞生多项新纪录，一批年轻选手表现亮眼，为后续国际大赛"
        "积累了宝贵经验。",
        "source": "微博热搜",
        "category": "体育",
        "hot": 612000,
        "url": "https://s.weibo.com/top/summary",
        "age_minutes": 73,
    },
    {
        "id": 6,
        "title": "CBA新赛季揭幕，年轻球员表现抢眼",
        "summary": "新赛季首轮多场比赛战至最后一刻，多名新秀交出亮眼数据，联赛竞争格局备受球迷期待。",
        "source": "今日头条",
        "category": "体育",
        "hot": 431000,
        "url": "https://www.toutiao.com/hot-event/hot-board/",
        "age_minutes": 95,
    },
    {
        "id": 7,
        "title": "多部现实题材影视剧热播，引发观众热议",
        "summary": "近期多部聚焦普通人生活的剧集口碑走高，真实细腻的表达方式带动相关话题持续登上热搜。",
        "source": "微博热搜",
        "category": "娱乐",
        "hot": 573000,
        "url": "https://s.weibo.com/top/summary",
        "age_minutes": 118,
    },
    {
        "id": 8,
        "title": "全国多地气温下降，气象部门提醒注意防寒保暖",
        "summary": "受冷空气影响，北方多地迎来明显降温，部分地区伴有大风天气，气象部门提示关注临近预报、"
        "及时增添衣物。",
        "source": "百度热搜",
        "category": "社会",
        "hot": 522000,
        "url": "https://top.baidu.com/board?tab=realtime",
        "age_minutes": 34,
    },
    {
        "id": 9,
        "title": "城市公共交通迎来升级，多条地铁新线开通运营",
        "summary": "多个城市新一轮轨道交通线路投入运营，换乘更加便利，沿线居民的日常通勤时间明显缩短。",
        "source": "知乎热榜",
        "category": "社会",
        "hot": 389000,
        "url": "https://www.zhihu.com/hot",
        "age_minutes": 152,
    },
    {
        "id": 10,
        "title": "全球气候大会聚焦减排合作，多国公布新承诺",
        "summary": "与会各方围绕能源转型、绿色金融等议题展开磋商，多国在会上提出阶段性减排目标与资金支持计划。",
        "source": "今日头条",
        "category": "国际",
        "hot": 347000,
        "url": "https://www.toutiao.com/hot-event/hot-board/",
        "age_minutes": 176,
    },
    {
        "id": 11,
        "title": "专家提示秋冬流感高发，建议重点人群及时接种疫苗",
        "summary": "随着气温转凉，呼吸道传染病进入高发期，专家建议老人、儿童等重点人群尽早接种疫苗，"
        "并保持良好卫生习惯。",
        "source": "百度热搜",
        "category": "健康",
        "hot": 468000,
        "url": "https://top.baidu.com/board?tab=realtime",
        "age_minutes": 67,
    },
    {
        "id": 12,
        "title": "高校毕业生就业服务季启动，多场招聘活动陆续开展",
        "summary": "各地人社部门联合高校推出一系列专场招聘与就业指导活动，覆盖线上线下多种形式，"
        "帮助毕业生拓宽求职渠道。",
        "source": "知乎热榜",
        "category": "教育",
        "hot": 302000,
        "url": "https://www.zhihu.com/hot",
        "age_minutes": 203,
    },
]


def serialize_news(item: dict) -> dict:
    """把内置榜单条目序列化为前端结构，并把「距今分钟数」换算成动态发布时间。"""
    published = datetime.now(timezone.utc) - timedelta(minutes=item.get("age_minutes", 0))
    return {
        "id": item["id"],
        "title": item["title"],
        "summary": item["summary"],
        "source": item["source"],
        "category": item["category"],
        "hot": item["hot"],
        "url": item["url"],
        "published_at": to_iso_utc(published),
    }


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
        "published_at": to_iso_utc(row[7]),
    }


# 每个来源最多取前 N 条，保证多来源均衡、不被单一榜单刷屏
_PER_SOURCE_ROWS = 8


@router.get("/hot")
async def get_hot_news(
    limit: int = Query(10, ge=1, le=50),
    category: str = Query("", description="按分类过滤，留空返回全部"),
    kind: str = Query("", description="按板块过滤：news 热点 / rank 榜单，留空返回全部"),
):
    """热点/榜单列表：优先读定时抓取的库内快照，空则回退内置榜单。"""
    category = category.strip()
    kind = kind.strip()
    try:
        async with db_conn() as conn:
            records = await conn.fetch(
                """
                SELECT id, source, category, title, summary, url, hot, fetched_at
                FROM (
                    SELECT id, source, category, title, summary, url, hot, fetched_at,
                           ROW_NUMBER() OVER (PARTITION BY source ORDER BY hot DESC, id ASC) AS rn
                    FROM hot_news
                    WHERE fetched_at > now() - interval '24 hours'
                      AND ($1 = '' OR category = $1)
                      AND ($2 = '' OR kind = $2)
                ) t
                WHERE rn <= $3
                ORDER BY rn ASC, hot DESC, id ASC
                LIMIT $4
                """,
                category,
                kind,
                _PER_SOURCE_ROWS,
                limit,
            )
        if records:
            updated = max((r[7] for r in records), default=datetime.now(timezone.utc))
            # 快照过期（如 Render 免费实例休眠后重启）时，非阻塞地在后台补抓
            if datetime.now(timezone.utc) - updated > timedelta(
                minutes=max(1, settings.NEWS_CRAWL_INTERVAL_MINUTES)
            ):
                trigger_background_crawl()
            return {
                "success": True,
                "source": "crawl",
                "updated_at": to_iso_utc(updated),
                "news": [serialize_db_row(r) for r in records],
            }
    except Exception as exc:  # noqa: BLE001 - 读库异常不应影响接口可用性
        print(f"⚠️ [NEWS] 读取热点库失败，回退内置榜单: {exc}")

    # 库内无数据：后台补抓一次，同时先返回内置榜单兜底
    trigger_background_crawl()

    # 回退：内置榜单
    items = [n for n in HOT_NEWS if not category or n["category"] == category]
    items = sorted(items, key=lambda x: x["hot"], reverse=True)[:limit]
    return {
        "success": True,
        "source": "bundled",
        "updated_at": to_iso_utc(datetime.now(timezone.utc)),
        "news": [serialize_news(i) for i in items],
    }


@router.get("/categories")
async def get_news_categories():
    """返回可用的热点分类（优先取库内实际分类，空则回退内置榜单）。"""
    categories: list[str] = []
    try:
        async with db_conn() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT category FROM hot_news "
                "WHERE fetched_at > now() - interval '24 hours' AND category <> '' "
                "ORDER BY category"
            )
        categories = [r[0] for r in rows]
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [NEWS] 读取热点分类失败，回退内置榜单: {exc}")

    if not categories:
        for item in HOT_NEWS:
            if item["category"] not in categories:
                categories.append(item["category"])
    return {"success": True, "categories": categories}


@router.post("/crawl")
async def trigger_crawl(_: dict = Depends(get_current_admin)):
    """手动触发一次热点抓取（仅管理员），便于立即刷新而不必等定时任务。"""
    count = await crawl_all()
    return {"success": True, "count": count, "message": f"本轮已抓取 {count} 条热点"}


@router.get("/{news_id}")
async def get_news_detail(news_id: int):
    """热点详情：先查库内快照，未命中再查内置榜单。"""
    try:
        async with db_conn() as conn:
            row = await conn.fetchrow(
                "SELECT id, source, category, title, summary, url, hot, fetched_at "
                "FROM hot_news WHERE id = $1",
                news_id,
            )
        if row:
            return {"success": True, "news": serialize_db_row(row)}
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ [NEWS] 读取热点详情失败: {exc}")

    for item in HOT_NEWS:
        if item["id"] == news_id:
            return {"success": True, "news": serialize_news(item)}
    raise HTTPException(status_code=404, detail="未找到该热点新闻")

