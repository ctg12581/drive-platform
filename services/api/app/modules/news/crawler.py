# app/modules/news/crawler.py
# 热点新闻定时爬虫：周期性抓取多个公开来源，落库为快照，供 /news/hot 读取。
#
# 设计要点：
#   - 只用标准库 urllib / xml（无需新增依赖），在线程中执行避免阻塞事件循环；
#   - 来源以「全球可达的 RSS/聚合源」为主（Google 新闻中文、BBC 中文、36氪、vvhan 等），
#     国内直连热榜（微博/知乎/百度/头条）为辅——因为部署在 Render（美国机房），直连常被地域限制；
#   - 各来源逐条容错，任一来源失败不影响其它；每轮成功则「整表替换」为最新快照（原子事务）；
#   - 若本轮一条都没抓到（如外网不可达），保留旧数据，接口再空则回退到内置榜单。
import asyncio
import gzip
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from app.core.config import settings
from app.core.db import db_transaction

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# 关键词 -> 分类，用于给抓回来的标题自动归类（前端按分类上色）。
CATEGORY_KEYWORDS = {
    "科技": ["AI", "人工智能", "大模型", "芯片", "手机", "科技", "互联网", "华为", "苹果",
             "航天", "机器人", "软件", "数据", "算法", "5G", "6G", "半导体", "新能源车"],
    "财经": ["股", "基金", "经济", "金融", "楼市", "房价", "央行", "利率", "汇率", "消费",
             "上市", "财报", "GDP", "通胀", "黄金", "油价"],
    "体育": ["足球", "篮球", "CBA", "NBA", "国足", "奥运", "田径", "乒乓", "羽毛球", "网球",
             "联赛", "冠军", "世界杯", "亚运"],
    "娱乐": ["电影", "电视剧", "综艺", "明星", "歌手", "演唱会", "票房", "剧集", "演员",
             "导演", "音乐", "热播"],
    "健康": ["流感", "疫苗", "医院", "疾病", "健康", "养生", "医生", "病毒", "药品", "医保"],
    "教育": ["高校", "高考", "考研", "就业", "招聘", "毕业生", "学生", "教育", "考试", "大学"],
    "国际": ["美国", "俄罗斯", "欧洲", "日本", "韩国", "联合国", "全球", "国际", "外交", "乌克兰"],
    "社会": ["天气", "降温", "台风", "地铁", "公交", "交通", "事故", "警方", "法院", "政策", "民生"],
}


def guess_category(title: str) -> str:
    """按关键词粗略给标题分类，未命中归为「热点」。"""
    text = title or ""
    for category, words in CATEGORY_KEYWORDS.items():
        for w in words:
            if w in text:
                return category
    return "热点"


def _parse_hot(value) -> int:
    """把「123 万热度」「1.2亿」「1,234,567」等热度文本解析成整数。"""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).replace(",", "").replace(" ", "")
    match = re.search(r"([\d.]+)\s*(亿|万)?", text)
    if not match:
        return 0
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "亿":
        number *= 100_000_000
    elif unit == "万":
        number *= 10_000
    return int(number)


def _http_get_text(url: str, timeout: int = 10, referer: str = "", accept: str = "*/*") -> str:
    """GET 一个 URL 并返回文本，自动处理 gzip 压缩。"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        encoding = (response.headers.get("Content-Encoding") or "").lower()
    if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", errors="ignore")


def _http_get_json(url: str, timeout: int = 8, referer: str = "") -> dict:
    """GET 一个返回 JSON 的接口。"""
    text = _http_get_text(url, timeout, referer, "application/json, text/plain, */*")
    return json.loads(text)


def _strip_html(raw: str) -> str:
    """去掉摘要里的 HTML 标签与多余空白。"""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _child_text(node, name: str) -> str:
    """取子节点文本（忽略 XML 命名空间）。"""
    for child in node:
        if child.tag.split("}")[-1] == name:
            return (child.text or "").strip()
    return ""


def _child_link(node) -> str:
    """兼容 RSS(<link>文本) 与 Atom(<link href=...>) 的链接提取。"""
    for child in node:
        if child.tag.split("}")[-1] == "link":
            href = child.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def parse_rss(text: str) -> list[dict]:
    """解析 RSS/Atom 文本（Google 新闻、BBC 中文、36氪等），输出统一结构。

    RSS 无热度字段，hot 记为 0，靠 rank 保持来源内顺序。
    """
    root = ET.fromstring(text)
    nodes = [n for n in root.iter() if n.tag.split("}")[-1] in ("item", "entry")]
    items: list[dict] = []
    for idx, node in enumerate(nodes):
        title = _child_text(node, "title")
        if not title:
            continue
        link = _child_link(node)
        summary = _strip_html(_child_text(node, "description") or _child_text(node, "summary"))
        items.append({
            "external_id": link or title,
            "title": title,
            "summary": summary[:300],
            "url": link,
            "hot": 0,
            "rank": idx + 1,
        })
    return items


# ---------------------------------------------------------------------------
# 各来源解析器：统一输出 [{external_id,title,summary,url,hot,rank}, ...]
# ---------------------------------------------------------------------------
def parse_weibo(data: dict) -> list[dict]:
    realtime = (data.get("data") or {}).get("realtime") or []
    items: list[dict] = []
    for idx, it in enumerate(realtime):
        word = (it.get("word") or "").strip()
        if not word or it.get("is_ad"):
            continue
        items.append({
            "external_id": word,
            "title": word,
            "summary": it.get("note") or "",
            "url": "https://s.weibo.com/weibo?q=" + urllib.parse.quote(f"#{word}#"),
            "hot": _parse_hot(it.get("num") or it.get("raw_hot")),
            "rank": idx + 1,
        })
    return items


def parse_zhihu(data: dict) -> list[dict]:
    items: list[dict] = []
    for idx, it in enumerate(data.get("data") or []):
        target = it.get("target") or {}
        title = (target.get("title") or "").strip()
        if not title:
            continue
        question_id = target.get("id")
        items.append({
            "external_id": str(question_id or title),
            "title": title,
            "summary": (target.get("excerpt") or "").strip(),
            "url": f"https://www.zhihu.com/question/{question_id}" if question_id else "https://www.zhihu.com/hot",
            "hot": _parse_hot(it.get("detail_text")),
            "rank": idx + 1,
        })
    return items


def parse_baidu(data: dict) -> list[dict]:
    items: list[dict] = []
    cards = (data.get("data") or {}).get("cards") or []
    idx = 0
    for card in cards:
        for it in card.get("content") or []:
            word = (it.get("word") or it.get("query") or "").strip()
            if not word:
                continue
            idx += 1
            items.append({
                "external_id": word,
                "title": word,
                "summary": (it.get("desc") or "").strip(),
                "url": it.get("url") or "https://top.baidu.com/board?tab=realtime",
                "hot": _parse_hot(it.get("hotScore")),
                "rank": idx,
            })
    return items


def parse_toutiao(data: dict) -> list[dict]:
    items: list[dict] = []
    for idx, it in enumerate(data.get("data") or []):
        title = (it.get("Title") or it.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "external_id": str(it.get("ClusterIdStr") or it.get("ClusterId") or title),
            "title": title,
            "summary": "",
            "url": it.get("Url") or it.get("url") or "https://www.toutiao.com/hot-event/hot-board/",
            "hot": _parse_hot(it.get("HotValue") or it.get("hot")),
            "rank": idx + 1,
        })
    return items


def parse_vvhan(data: dict) -> list[dict]:
    """vvhan 聚合源：{success, data:[{title, hot, url, index}]}。"""
    items: list[dict] = []
    for idx, it in enumerate(data.get("data") or []):
        title = (it.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "external_id": title,
            "title": title,
            "summary": (it.get("desc") or "").strip(),
            "url": it.get("url") or it.get("mobilUrl") or "",
            "hot": _parse_hot(it.get("hot")),
            "rank": int(it.get("index") or (idx + 1)),
        })
    return items


# 来源清单：
#   kind=rss 走 XML 解析，kind=json 走 JSON 解析。
#   顺序即优先级；RSS/聚合源在前（部署在 Render 美国机房也能稳定访问），
#   国内直连热榜在后（对境外 IP 常返回 403/限额，失败会自动跳过）。
SOURCES = [
    # —— 全球可达的 RSS 源（Render 上最稳）——
    {"name": "Google新闻", "kind": "rss",
     "url": "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
     "parser": parse_rss},
    {"name": "BBC中文", "kind": "rss",
     "url": "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml",
     "parser": parse_rss},
    {"name": "36氪", "kind": "rss",
     "url": "https://36kr.com/feed",
     "parser": parse_rss},
    # —— 聚合源兜底（国内热榜聚合，境外访问成功率较高）——
    {"name": "微博热搜", "kind": "json", "url": "https://api.vvhan.com/api/hotlist/wbHot",
     "parser": parse_vvhan, "referer": "https://api.vvhan.com/"},
    {"name": "知乎热榜", "kind": "json", "url": "https://api.vvhan.com/api/hotlist/zhihuHot",
     "parser": parse_vvhan, "referer": "https://api.vvhan.com/"},
    {"name": "百度热搜", "kind": "json", "url": "https://api.vvhan.com/api/hotlist/baiduRD",
     "parser": parse_vvhan, "referer": "https://api.vvhan.com/"},
    {"name": "今日头条", "kind": "json", "url": "https://api.vvhan.com/api/hotlist/toutiao",
     "parser": parse_vvhan, "referer": "https://api.vvhan.com/"},
    # —— 国内直连（国内环境可用；Render 上失败则跳过）——
    {"name": "微博热搜", "kind": "json", "url": "https://weibo.com/ajax/side/hotSearch",
     "parser": parse_weibo, "referer": "https://weibo.com/"},
    {"name": "知乎热榜", "kind": "json",
     "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true",
     "parser": parse_zhihu, "referer": "https://www.zhihu.com/hot"},
    {"name": "百度热搜", "kind": "json", "url": "https://top.baidu.com/api/board?platform=wise&tab=realtime",
     "parser": parse_baidu, "referer": "https://top.baidu.com/board?tab=realtime"},
    {"name": "今日头条", "kind": "json", "url": "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
     "parser": parse_toutiao, "referer": "https://www.toutiao.com/"},
]

_CRAWL_LOCK = asyncio.Lock()
# 每个来源最多保留的条数，避免单源刷屏
MAX_PER_SOURCE = 30


async def _fetch_one(cfg: dict) -> list[dict]:
    if cfg.get("kind") == "rss":
        text = await asyncio.to_thread(
            _http_get_text, cfg["url"], 10, cfg.get("referer", ""), "application/rss+xml, application/xml, text/xml, */*"
        )
        parsed = cfg["parser"](text) or []
    else:
        data = await asyncio.to_thread(_http_get_json, cfg["url"], 8, cfg.get("referer", ""))
        parsed = cfg["parser"](data) or []
    for item in parsed:
        item["source"] = cfg["name"]
        item["category"] = guess_category(item.get("title", ""))
        # 区分「热点新闻」(news) 与「热榜排名」(rank)：RSS 视为新闻，热榜接口视为榜单
        item["kind"] = cfg.get("section") or ("news" if cfg.get("kind") == "rss" else "rank")
        if not item.get("summary"):
            item["summary"] = ""
    return parsed


async def _persist(items: list[dict]):
    """整表替换为最新快照（单事务，保证读端不会读到半截数据）。"""
    rows = [
        (
            it["source"],
            (it.get("kind") or "rank")[:10],
            (it.get("category") or "热点")[:30],
            (it.get("title") or "")[:500],
            (it.get("summary") or "")[:1000],
            (it.get("url") or "")[:1000],
            int(it.get("hot") or 0),
            str(it.get("external_id") or "")[:200],
            int(it.get("rank") or 0),
        )
        for it in items
    ]
    async with db_transaction() as conn:
        await conn.execute("DELETE FROM hot_news")
        await conn.executemany(
            "INSERT INTO hot_news (source, kind, category, title, summary, url, hot, external_id, rank_index, fetched_at) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now())",
            rows,
        )


async def crawl_all() -> int:
    """抓取全部来源并落库，返回本轮入库条数。"""
    async with _CRAWL_LOCK:
        tasks = [asyncio.create_task(_fetch_one(cfg)) for cfg in SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        collected: list[dict] = []
        for cfg, result in zip(SOURCES, results):
            if isinstance(result, Exception):
                print(f"⚠️ [NEWS] 抓取「{cfg['name']}」失败: {result}")
                continue
            collected.extend(result)

        # 同一来源内按 external_id/title 去重，保留热度更高的
        dedup: dict[tuple[str, str], dict] = {}
        for item in collected:
            key = (item["source"], item.get("external_id") or item["title"])
            if key not in dedup or int(item.get("hot") or 0) > int(dedup[key].get("hot") or 0):
                dedup[key] = item
        unique = list(dedup.values())

        # 每个来源截断，再合并
        per_source: dict[str, list[dict]] = {}
        for item in unique:
            per_source.setdefault(item["source"], []).append(item)
        final: list[dict] = []
        for _, group in per_source.items():
            group.sort(key=lambda x: int(x.get("hot") or 0), reverse=True)
            final.extend(group[:MAX_PER_SOURCE])

        if not final:
            print("⚠️ [NEWS] 本轮未抓取到任何热点，保留上一轮数据")
            return 0

        await _persist(final)
        print(f"✅ [NEWS] 热点快照已更新：{len(final)} 条")
        return len(final)


async def crawl_loop():
    """后台循环：启动后先抓一次，之后按配置间隔刷新。"""
    interval = max(1, int(settings.NEWS_CRAWL_INTERVAL_MINUTES)) * 60
    await asyncio.sleep(5)  # 等建表/启动稳定后再抓
    while True:
        try:
            await crawl_all()
        except Exception as exc:  # noqa: BLE001 - 定时任务不能因单轮异常退出
            print(f"❌ [NEWS] 定时抓取异常: {exc}")
        await asyncio.sleep(interval)


# —— 供接口层调用：快照过期时在后台补抓（应对 Render 免费实例休眠导致定时器停摆）——
_bg_task: asyncio.Task | None = None
_last_trigger = 0.0


def trigger_background_crawl(min_interval_seconds: int = 60) -> None:
    """非阻塞地触发一次后台抓取；已有任务在跑或距上次触发不足 min_interval 时跳过。"""
    global _bg_task, _last_trigger
    if _bg_task is not None and not _bg_task.done():
        return
    now = time.monotonic()
    if now - _last_trigger < min_interval_seconds:
        return
    _last_trigger = now
    _bg_task = asyncio.create_task(crawl_all())

