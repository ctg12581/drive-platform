# app/modules/anime/crawler.py
# 动漫人物图鉴定时爬虫：抓取「中 · 美 · 日」三地动画角色，整表刷新到 anime_characters。
#
# 数据源（均为公开、免 Key 接口，只用标准库 urllib，无新增依赖）：
#   - 日漫 / 国漫：AniList GraphQL（countryOfOrigin = JP / CN，按人气排序，取作品主角）
#   - 美漫：      TVmaze 公开 API（按人气/经典动画剧集种子表逐部抓取角色与配音）
#
# 设计要点：
#   - 单次抓取「尽可能多」：分页拉取高人气作品，每个地区最多保留 ANIME_CRAWL_MAX_PER_REGION 个角色；
#   - 每个来源逐条容错，任一来源/作品失败不影响其它；
#   - 每轮成功则「整表替换」为最新快照（原子事务），失败保留旧数据；
#   - 抓取在线程中执行，避免阻塞事件循环；带简单重试与限速，尊重来源接口频率。
import argparse
import asyncio
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from app.core.config import settings
from app.core.db import db_transaction, init_global_tables, init_pool, close_pool

USER_AGENT = (
    "drive-platform-anime-crawler/1.0 "
    "(+https://github.com/ctg12581; contact: dev@example.com)"
)
ANILIST_URL = "https://graphql.anilist.co"
TVMAZE_BASE = "https://api.tvmaze.com"

# 每部美漫剧集最多取多少个角色（取 cast 前若干位，保证多部作品都有覆盖，避免被单部剧刷屏）
MAX_CAST_PER_SHOW = max(1, int(settings.ANIME_CRAWL_MAX_CAST_PER_SHOW))

REGION_FLAG = {"jp": "🇯🇵", "cn": "🇨🇳", "us": "🇺🇸"}
REGION_TAG = {"jp": "日漫", "cn": "国漫", "us": "美漫"}

# AniList / TVmaze 的英文题材 -> 中文标签
GENRE_ZH = {
    "Action": "动作", "Adventure": "冒险", "Comedy": "喜剧", "Drama": "剧情",
    "Ecchi": "福利", "Fantasy": "奇幻", "Horror": "恐怖", "Mahou Shoujo": "魔法少女",
    "Mecha": "机甲", "Music": "音乐", "Mystery": "悬疑", "Psychological": "心理",
    "Romance": "恋爱", "Sci-Fi": "科幻", "Slice of Life": "日常", "Sports": "运动",
    "Supernatural": "超自然", "Thriller": "惊悚", "School": "校园", "Space": "太空",
    "Military": "军事", "Historical": "历史", "Family": "家庭", "Kids": "少儿",
    "Anime": "动画", "Children": "少儿", "Food": "美食", "Medical": "医疗",
    "Legal": "律政", "Crime": "犯罪", "Espionage": "谍战",
    "Science Fiction": "科幻", "War": "战争", "Western": "西部",
}

# AniList 作品查询：一次取回作品 + 其角色 + 主配音，避免逐部请求
ANILIST_QUERY = """
query ($page: Int, $perPage: Int, $chars: Int, $country: CountryCode) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage }
    media(type: ANIME, countryOfOrigin: $country, sort: POPULARITY_DESC, isAdult: false) {
      id
      title { romaji native english }
      popularity
      genres
      characters(sort: [ROLE, RELEVANCE], perPage: $chars) {
        edges {
          node { id name { full native } image { large medium } description(asHtml: false) }
          va: voiceActors { name { full } }
        }
      }
    }
  }
}
"""

# 美国经典 / 人气动画剧集种子（TVmaze 按剧名检索，能覆盖大量美漫角色）
TVMAZE_SHOWS = [
    # 成人 / 黄金档动画
    "The Simpsons", "Family Guy", "South Park", "Bob's Burgers", "Futurama",
    "King of the Hill", "Beavis and Butt-Head", "Daria", "Disenchantment",
    "Inside Job", "Solar Opposites", "Big Mouth", "Human Resources", "Tuca & Bertie",
    "Central Park", "Duncanville", "The Great North", "Archer", "BoJack Horseman",
    "Rick and Morty", "Final Space", "Harley Quinn", "Invincible", "Primal", "Undone",
    # 儿童 / 合家欢
    "SpongeBob SquarePants", "The Patrick Star Show", "Kamp Koral",
    "Adventure Time", "Gravity Falls", "Regular Show", "Steven Universe",
    "The Powerpuff Girls", "Dexter's Laboratory", "Samurai Jack", "Sym-Bionic Titan",
    "Generator Rex", "The Secret Saturdays", "Codename: Kids Next Door",
    "Foster's Home for Imaginary Friends", "The Marvelous Misadventures of Flapjack",
    "Chowder", "The Grim Adventures of Billy & Mandy", "My Life as a Teenage Robot",
    "El Tigre: The Adventures of Manny Rivera", "The Mighty B!", "Fanboy & Chum Chum",
    "T.U.F.F. Puppy", "Sanjay and Craig", "Harvey Beaks", "The Loud House",
    "The Casagrandes", "Middlemost Post", "Wander Over Yonder",
    "Star vs. the Forces of Evil", "The Owl House", "Amphibia", "Big City Greens",
    "Craig of the Creek", "Uncle Grandpa", "Clarence", "OK K.O.! Let's Be Heroes",
    "Summer Camp Island", "We Bare Bears", "The Amazing World of Gumball",
    "Over the Garden Wall", "She-Ra and the Princesses of Power",
    "Kipo and the Age of Wonderbeasts", "Trollhunters", "Voltron: Legendary Defender",
    "Castlevania", "Masters of the Universe: Revelation",
    # 经典怀旧
    "Scooby-Doo, Where Are You!", "Looney Tunes", "Tom and Jerry",
    "The Flintstones", "The Jetsons", "The Smurfs", "Alvin and the Chipmunks",
    "Garfield and Friends", "The Rocky and Bullwinkle Show", "Underdog",
    "George of the Jungle", "Jonny Quest", "Space Ghost", "He-Man and the Masters of the Universe",
    "She-Ra: Princess of Power", "G.I. Joe", "Transformers", "Jem and the Holograms",
    "Rainbow Brite", "Care Bears", "Strawberry Shortcake", "Woody Woodpecker",
    "Rugrats", "Hey Arnold!", "Doug", "Recess", "The Ren & Stimpy Show",
    "Rocko's Modern Life", "Aaahh!!! Real Monsters", "The Wild Thornberrys",
    "CatDog", "Rocket Power", "The Angry Beavers", "KaBlam!", "Pepper Ann",
    "The Proud Family", "Lilo & Stitch: The Series", "American Dragon: Jake Long",
    # 超级英雄 / 游戏改编 / 其他
    "Batman: The Animated Series", "Superman: The Animated Series", "Justice League",
    "Teen Titans", "Teen Titans Go!", "Batman Beyond", "Static Shock",
    "X-Men: The Animated Series", "Spider-Man: The Animated Series",
    "The Avengers: Earth's Mightiest Heroes", "Ben 10",
    "Avatar: The Last Airbender", "The Legend of Korra", "Phineas and Ferb",
    "Kim Possible", "DuckTales", "Mickey Mouse Clubhouse", "Winnie the Pooh",
    "My Little Pony: Friendship Is Magic", "PAW Patrol", "Danny Phantom",
    "The Fairly OddParents", "Jimmy Neutron: Boy Genius", "Invader Zim",
    "Courage the Cowardly Dog", "Ed, Edd n Eddy", "Johnny Bravo",
]


# ---------------------------------------------------------------------------
# HTTP 工具（标准库 urllib，自动处理 gzip 与重试）
# ---------------------------------------------------------------------------
def _http_json(url: str, data: bytes | None = None, timeout: int = 30, retries: int = 5) -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                encoding = (resp.headers.get("Content-Encoding") or "").lower()
            if encoding == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8", "ignore"))
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 429:  # 限流：尊重 Retry-After，退避后重试
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    wait = float(retry_after) if retry_after else 15.0 * (attempt + 1)
                except ValueError:
                    wait = 15.0 * (attempt + 1)
                print(f"⚠️ [ANIME] 触发限流(429)，{wait:.0f}s 后重试：{url.split('?')[0]}")
                time.sleep(min(wait, 60))
                continue
            if exc.code in (500, 502, 503, 504):
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_exc or RuntimeError(f"请求失败: {url}")


def _clean_text(raw: str) -> str:
    """清理 AniList/HTML 富文本：去剧透标记、Markdown 链接/图片、HTML 标签，压空白。"""
    if not raw:
        return ""
    text = re.sub(r"~!.*?!~", "", raw, flags=re.S)          # 剧透包裹
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)         # 图片
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)     # 链接取文字
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)                      # HTML 标签
    text = re.sub(r"__|\*\*|`", "", text)                    # 强调符号
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _pick_voice(voice_actors: list, region: str) -> str:
    """取第一位配音（AniList 按相关度排序，首位通常是原生语言主配音）。"""
    for va in voice_actors or []:
        name = (va.get("name") or {}).get("full")
        if name:
            return name
    return ""


def _translate_tags(genres: list, region: str) -> list:
    tags = [GENRE_ZH.get(g, g) for g in (genres or []) if g and GENRE_ZH.get(g, g)]
    region_tag = REGION_TAG.get(region)
    if region_tag and region_tag not in tags:
        tags.insert(0, region_tag)
    # 去重且保持顺序
    return list(dict.fromkeys(tags))


# ---------------------------------------------------------------------------
# AniList：日漫 / 国漫
# ---------------------------------------------------------------------------
def _crawl_anilist_sync(country: str, region: str, max_per_region: int,
                        chars_per_media: int = 10, media_per_page: int = 10,
                        max_pages: int = 25, page_sleep: float = 2.5) -> list[dict]:
    collected: dict[str, dict] = {}
    for page in range(1, max_pages + 1):
        payload = _http_json(
            ANILIST_URL,
            data=json.dumps({
                "query": ANILIST_QUERY,
                "variables": {
                    "page": page,
                    "perPage": media_per_page,
                    "chars": chars_per_media,
                    "country": country,
                },
            }).encode("utf-8"),
        )
        if payload.get("errors"):
            print(f"⚠️ [ANIME] AniList {country} 第 {page} 页报错: {payload['errors']}")
            break
        page_data = (payload.get("data") or {}).get("Page") or {}
        media = page_data.get("media") or []
        if not media:
            break
        for m in media:
            popularity = int(m.get("popularity") or 0)
            title = m.get("title") or {}
            work = (title.get("native") or title.get("romaji") or "").strip()
            work_en = (title.get("english") or title.get("romaji") or "").strip()
            tags = _translate_tags(m.get("genres") or [], region)
            edges = ((m.get("characters") or {}).get("edges")) or []
            for edge in edges:
                node = edge.get("node") or {}
                cid = node.get("id")
                if not cid:
                    continue
                external_id = f"anilist:{cid}"
                if external_id in collected:  # 同一角色只保留首次（人气更高的作品）
                    continue
                names = node.get("name") or {}
                name = (names.get("native") or names.get("full") or "").strip()
                name_en = (names.get("full") or "").strip()
                if not name:
                    continue
                image = node.get("image") or {}
                description = _clean_text(node.get("description") or "")[:600]
                collected[external_id] = {
                    "external_id": external_id,
                    "region": region,
                    "name": name,
                    "name_en": name_en,
                    "work": work,
                    "work_en": work_en,
                    "avatar": REGION_FLAG.get(region, "🎬"),
                    "image_url": (image.get("large") or image.get("medium") or "").strip(),
                    "tags": tags,
                    "voice_actor": _pick_voice(edge.get("va") or [], region),
                    "personality": "",
                    "introduction": description or f"出自《{work}》的角色。",
                    "quote": "",
                    "source": "anilist",
                    "popularity": popularity,
                }
        if not page_data.get("pageInfo", {}).get("hasNextPage"):
            break
        if max_per_region and len(collected) >= max_per_region:  # 达到上限则提前停止
            break
        time.sleep(page_sleep)  # 限速，AniList 免费额度约 30 次/分钟

    items = sorted(collected.values(), key=lambda x: x["popularity"], reverse=True)
    return items[:max_per_region] if max_per_region else items


async def crawl_anilist(country: str, region: str, max_per_region: int) -> list[dict]:
    return await asyncio.to_thread(
        _crawl_anilist_sync,
        country,
        region,
        max_per_region,
        max(1, int(settings.ANIME_CRAWL_CHARS_PER_MEDIA)),
        10,
        max(1, int(settings.ANIME_CRAWL_MAX_PAGES_PER_REGION)),
    )


# ---------------------------------------------------------------------------
# TVmaze：美漫
# ---------------------------------------------------------------------------
def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "x"


def _crawl_tvmaze_sync(max_per_region: int) -> list[dict]:
    collected: dict[str, dict] = {}
    for show_name in TVMAZE_SHOWS:
        try:
            show = _http_json(f"{TVMAZE_BASE}/singlesearch/shows?q={urllib.parse.quote(show_name)}")
        except Exception as exc:  # noqa: BLE001 - 单个剧集失败不影响整体
            print(f"⚠️ [ANIME] TVmaze 检索「{show_name}」失败: {exc}")
            continue
        if not show or not show.get("id"):
            continue
        show_id = show["id"]
        work = (show.get("name") or show_name).strip()
        genres = _translate_tags(show.get("genres") or [], "us")
        rating = (show.get("rating") or {}).get("average")
        popularity = int(rating * 10) if rating else int(show.get("weight") or 0)
        try:
            cast = _http_json(f"{TVMAZE_BASE}/shows/{show_id}/cast")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ [ANIME] TVmaze 获取「{work}」角色失败: {exc}")
            continue
        for entry in (cast or [])[:MAX_CAST_PER_SHOW]:
            character = entry.get("character") or {}
            person = entry.get("person") or {}
            char_name = (character.get("name") or "").strip()
            if not char_name:
                continue
            external_id = f"tvmaze:{show_id}:{_slug(char_name)}"
            if external_id in collected:
                continue
            char_image = (character.get("image") or {}).get("medium") or ""
            person_image = (person.get("image") or {}).get("medium") or ""
            person_name = (person.get("name") or "").strip()
            intro = f"出自美国动画《{work}》的角色"
            intro += f"，由 {person_name} 配音。" if person_name else "。"
            collected[external_id] = {
                "external_id": external_id,
                "region": "us",
                "name": char_name,
                "name_en": char_name,
                "work": work,
                "work_en": work,
                "avatar": REGION_FLAG.get("us", "🎬"),
                "image_url": (char_image or person_image).strip(),
                "tags": list(genres),
                "voice_actor": person_name,
                "personality": "",
                "introduction": intro,
                "quote": "",
                "source": "tvmaze",
                "popularity": popularity,
            }
        if max_per_region and len(collected) >= max_per_region:  # 达到上限则提前停止
            break
        time.sleep(0.25)  # 限速，TVmaze 免费接口约 20 次/10 秒

    items = sorted(collected.values(), key=lambda x: x["popularity"], reverse=True)
    return items[:max_per_region] if max_per_region else items


async def crawl_tvmaze(max_per_region: int) -> list[dict]:
    return await asyncio.to_thread(_crawl_tvmaze_sync, max_per_region)


# ---------------------------------------------------------------------------
# 汇总 / 落库
# ---------------------------------------------------------------------------
_CRAWL_LOCK = asyncio.Lock()


async def collect_all(max_per_region: int | None = None) -> tuple[dict[str, list[dict]], dict[str, str]]:
    """抓取三地角色，返回 ({region: 角色列表}, {失败region: 原因})。

    AniList 两个地区串行 + 限速请求，避免并发触发 429；TVmaze 与 AniList 并行。
    max_per_region=0 表示不限制。
    """
    raw_cap = max_per_region if max_per_region is not None else settings.ANIME_CRAWL_MAX_PER_REGION
    cap = max(0, int(raw_cap))  # 0 = 不限制

    results: dict[str, list[dict]] = {}
    failures: dict[str, str] = {}

    # 美漫与 AniList 并行（TVmaze 与 AniList 互不影响）
    us_task = asyncio.create_task(crawl_tvmaze(cap))

    # 日漫 / 国漫串行，避免两个 AniList 请求流同时打爆限流
    for country, region, label in (("JP", "jp", "日本"), ("CN", "cn", "国产")):
        try:
            items = await crawl_anilist(country, region, cap)
            results[region] = items
            print(f"✅ [ANIME] 来源「AniList · {label}」抓取 {len(items)} 个角色")
        except Exception as exc:  # noqa: BLE001 - 单地区失败保留旧数据
            failures[region] = str(exc)
            print(f"⚠️ [ANIME] 来源「AniList · {label}」抓取失败: {exc}")

    try:
        us_items = await us_task
        results["us"] = us_items
        print(f"✅ [ANIME] 来源「TVmaze · 美国」抓取 {len(us_items)} 个角色")
    except Exception as exc:  # noqa: BLE001
        failures["us"] = str(exc)
        print(f"⚠️ [ANIME] 来源「TVmaze · 美国」抓取失败: {exc}")

    return results, failures


async def _persist(items: list[dict], regions: set[str]) -> None:
    """按地区替换快照：只删除并重写本次成功的地区，失败地区保留旧数据（单事务）。"""
    if not regions:
        return
    rows = [
        (
            (it.get("external_id") or "")[:80],
            (it.get("region") or "")[:8],
            (it.get("name") or "")[:120],
            (it.get("name_en") or "")[:160],
            (it.get("work") or "")[:200],
            (it.get("work_en") or "")[:200],
            (it.get("avatar") or "")[:16],
            (it.get("image_url") or "")[:1000],
            it.get("tags") or [],
            (it.get("voice_actor") or "")[:200],
            it.get("personality") or "",
            it.get("introduction") or "",
            it.get("quote") or "",
            (it.get("source") or "")[:20],
            int(it.get("popularity") or 0),
        )
        for it in items
        if it.get("region") in regions
    ]
    async with db_transaction() as conn:
        await conn.execute("DELETE FROM anime_characters WHERE region = ANY($1::text[])", list(regions))
        if rows:
            await conn.executemany(
                "INSERT INTO anime_characters "
                "(external_id, region, name, name_en, work, work_en, avatar, image_url, tags, "
                " voice_actor, personality, introduction, quote, source, popularity, fetched_at) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15, now())",
                rows,
            )


async def crawl_all(max_per_region: int | None = None, persist: bool = True) -> list[dict]:
    """抓取全部来源并（可选）落库，返回本轮抓到的角色列表。"""
    async with _CRAWL_LOCK:
        results, failures = await collect_all(max_per_region)
        # 全局去重（source + external_id）
        dedup: dict[str, dict] = {}
        for items in results.values():
            for item in items:
                dedup[f"{item['source']}:{item['external_id']}"] = item
        collected = list(dedup.values())
        if not collected:
            print("⚠️ [ANIME] 本轮未抓取到任何角色，保留上一轮数据")
            return []
        if persist:
            await _persist(collected, set(results.keys()))
        by_region: dict[str, int] = {}
        for it in collected:
            by_region[it["region"]] = by_region.get(it["region"], 0) + 1
        print(f"✅ [ANIME] 图鉴快照已更新：{len(collected)} 个角色 {by_region}")
        if failures:
            kept = ", ".join(sorted(failures))
            print(f"⚠️ [ANIME] 以下地区本轮失败、已保留旧数据：{kept}")
        return collected


async def crawl_loop():
    """后台循环：启动后先抓一次，之后按配置间隔刷新。"""
    interval = max(1, int(settings.ANIME_CRAWL_INTERVAL_MINUTES)) * 60
    await asyncio.sleep(10)  # 等建表/启动稳定后再抓
    while True:
        try:
            await crawl_all()
        except Exception as exc:  # noqa: BLE001 - 定时任务不能因单轮异常退出
            print(f"❌ [ANIME] 定时抓取异常: {exc}")
        await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# 命令行入口：python -m app.modules.anime.crawler [--dry-run] [--out out.json]
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="动漫人物图鉴爬虫（AniList + TVmaze）")
    parser.add_argument("--dry-run", action="store_true", help="只抓取不写数据库")
    parser.add_argument("--max-per-region", type=int, default=None, help="每地区最多保留角色数")
    parser.add_argument("--out", type=str, default="", help="抓取结果另存为 JSON 文件")
    return parser.parse_args(argv)


async def _main_async(args: argparse.Namespace) -> None:
    if args.dry_run:
        results, failures = await collect_all(args.max_per_region)
        items = [it for group in results.values() for it in group]
        if args.out and items:
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(items, fh, ensure_ascii=False, indent=2)
            print(f"💾 已写出 {args.out}（{len(items)} 条）")
        print(f"✅ [ANIME] 试运行完成：共 {len(items)} 个角色"
              + (f"，失败地区：{sorted(failures)}" if failures else ""))
        return
    await init_pool()
    try:
        await init_global_tables()
        await crawl_all(args.max_per_region)
    finally:
        await close_pool()


def main(argv: list[str] | None = None) -> None:
    asyncio.run(_main_async(_parse_args(argv if argv is not None else sys.argv[1:])))


if __name__ == "__main__":
    main()
