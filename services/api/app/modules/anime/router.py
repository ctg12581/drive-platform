# app/modules/anime/router.py
# 动漫人物介绍模块：内置一批「经典 + 热门」混合的动漫角色资料，
# 提供列表与详情只读接口，公开访问，无需登录鉴权。
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/anime", tags=["Anime 动漫人物介绍"])

# 内置动漫人物资料库（经典 + 热门混合）
ANIME_CHARACTERS = [
    {
        "id": 1,
        "name": "漩涡鸣人",
        "name_en": "Naruto Uzumaki",
        "work": "火影忍者",
        "work_en": "Naruto",
        "avatar": "🍥",
        "tags": ["热血", "励志", "忍者"],
        "voice_actor": "竹内顺子",
        "personality": "执着、乐观、永不放弃",
        "introduction": (
            "木叶隐村的忍者，体内封印着九尾妖狐。从小被村民排挤，却始终怀揣成为火影的梦想。"
            "他以超乎常人的毅力和行动力，一步步赢得认可，最终继承火之意志，成为受人爱戴的第七代火影。"
        ),
        "quote": "\"说到做到，就是我的忍道！\""
    },
    {
        "id": 2,
        "name": "毛利小五郎",
        "name_en": "Kogoro Mouri",
        "work": "名侦探柯南",
        "work_en": "Detective Conan",
        "avatar": "🕵️",
        "tags": ["推理", "侦探", "大叔"],
        "voice_actor": "神谷明 / 小山力也",
        "personality": "表面糊涂、关键时可靠",
        "introduction": (
            "东京著名的私人侦探，人称\"沉睡的小五郎\"。看似大大咧咧、嗜酒爱赌，"
            "但办案时往往在睡梦中\"灵光一现\"道破真相。是毛利兰的父亲，也是柯南的\"破案替身\"。"
        ),
        "quote": "\"真相只有一个...??\""
    },
    {
        "id": 3,
        "name": "樱木花道",
        "name_en": "Hanamichi Sakuragi",
        "work": "灌篮高手",
        "work_en": "Slam Dunk",
        "avatar": "🏀",
        "tags": ["运动", "篮球", "热血"],
        "voice_actor": "草尾毅",
        "personality": "自信爆棚、天赋异禀、不服输",
        "introduction": (
            "湘北高中篮球队的\"天才\"前锋，原是问题少年，为了追女孩加入篮球部。"
            "凭借惊人的弹跳力与学习能力，从门外汉成长为球队不可或缺的篮板王，"
            "用热血与汗水诠释了\"篮球人生\"。"
        ),
        "quote": "\"我是天才，哈哈哈哈哈！\""
    },
    {
        "id": 4,
        "name": "碇真嗣",
        "name_en": "Shinji Ikari",
        "work": "新世纪福音战士",
        "work_en": "Neon Genesis Evangelion",
        "avatar": "🤖",
        "tags": ["机战", "心理", "哲学"],
        "voice_actor": "绪方惠美",
        "personality": "内向、敏感、渴望被认可",
        "introduction": (
            "EVA 初号机驾驶员，性格内向而敏感，被父亲召唤驾驶 EVA 对抗使徒。"
            "他不断在逃避与现实之间挣扎，其复杂的心路历程成为 EVA 这部充满哲学思辨作品的核心。"
        ),
        "quote": "\"不能逃避，不能逃避，不能逃避！\""
    },
    {
        "id": 5,
        "name": "路飞",
        "name_en": "Monkey D. Luffy",
        "work": "海贼王",
        "work_en": "One Piece",
        "avatar": "🏴‍☠️",
        "tags": ["冒险", "热血", "伙伴"],
        "voice_actor": "田中真弓",
        "personality": "自由、纯粹、重情重义",
        "introduction": (
            "草帽海贼团船长，橡胶果实能力者，梦想成为海贼王。他天真自由、毫无心机，"
            "却对伙伴极度重视，为了他们可以不惜一切。一路航行，集结伙伴，追逐\"ONE PIECE\"。"
        ),
        "quote": "\"我是要成为海贼王的男人！\""
    },
    {
        "id": 6,
        "name": "龙猫小月与小梅",
        "name_en": "Satsuki & Mei Kusakabe",
        "work": "龙猫",
        "work_en": "My Neighbor Totoro",
        "avatar": "🌳",
        "tags": ["治愈", "奇幻", "童年"],
        "voice_actor": "坂本千夏 / 重井船人",
        "personality": "天真烂漫、充满好奇心",
        "introduction": (
            "《龙猫》中搬去乡下居住的两姐妹。妹妹小梅天真烂漫，发现了森林里的龙猫；"
            "姐姐小月则懂事坚强。她们的故事讲述了大自然与童年的纯真美好，是吉卜力最治愈的经典。"
        ),
        "quote": "\"龙猫巴士，快来接我们吧！\""
    },
    {
        "id": 7,
        "name": "五条悟",
        "name_en": "Satoru Gojo",
        "work": "咒术回战",
        "work_en": "Jujutsu Kaisen",
        "avatar": "🕶️",
        "tags": ["战斗", "咒术", "最强"],
        "voice_actor": "中村悠一",
        "personality": "强大自信、玩世不恭、护短",
        "introduction": (
            "东京咒术高专教师，被称作\"现代最强的咒术师\"，拥有\"无下限术式\"与\"六眼\"。"
            "外表轻佻爱玩，实则实力深不可测，对弟子们倾注心血，是咒术界公认的顶尖存在。"
        ),
        "quote": "\"全盛期，我当定了你的老师。\""
    },
    {
        "id": 8,
        "name": "三笠·阿克曼",
        "name_en": "Mikasa Ackerman",
        "work": "进击的巨人",
        "work_en": "Attack on Titan",
        "avatar": "⚔️",
        "tags": ["战斗", "立体机动", "守护"],
        "voice_actor": "石川由依",
        "personality": "冷静、坚韧、守护型",
        "introduction": (
            "调查兵团士兵，阿克曼家族的末裔，拥有超人般的战斗天赋。"
            "她外表冷峻，内心却无比珍视家人般的存在，一生都在为了守护重要之人而战斗。"
        ),
        "quote": "\"只要我还活着，就一定会保护你。\""
    },
    {
        "id": 9,
        "name": "灶门炭治郎",
        "name_en": "Tanjiro Kamado",
        "work": "鬼灭之刃",
        "work_en": "Demon Slayer",
        "avatar": "🗡️",
        "tags": ["热血", "亲情", "除恶"],
        "voice_actor": "花江夏树",
        "personality": "温柔、坚韧、充满同理心",
        "introduction": (
            "善良温柔的少年，一家惨遭鬼杀后，肩负起让变成鬼的妹妹祢豆子恢复人身的使命。"
            "他手持日之呼吸，加入鬼杀队，在斩鬼之路上对敌人也抱持着悲悯，是鬼灭之刃的灵魂人物。"
        ),
        "quote": "\"一起变强，绝不放弃。\""
    },
    {
        "id": 10,
        "name": "利威尔·阿克曼",
        "name_en": "Levi Ackerman",
        "work": "进击的巨人",
        "work_en": "Attack on Titan",
        "avatar": "🪓",
        "tags": ["战斗", "兵长", "洁癖"],
        "voice_actor": "神谷浩史",
        "personality": "冷酷、强大、外冷内热",
        "introduction": (
            "调查兵团特别作战班班长，被称为\"人类最强士兵\"。拥有无解的立体机动战斗技巧，"
            "外表冷酷寡言、有严重洁癖，实则内心珍视部下与同伴，是战场上最可靠的领袖。"
        ),
        "quote": "\"选择吧，后悔你的人生，或者认同你的人生。\""
    },
    {
        "id": 11,
        "name": "小智",
        "name_en": "Ash Ketchum",
        "work": "宝可梦",
        "work_en": "Pokémon",
        "avatar": "⚡",
        "tags": ["冒险", "伙伴", "成长"],
        "voice_actor": "松本梨香",
        "personality": "热情、勇敢、与宝可梦心灵相通",
        "introduction": (
            "真新镇出身、梦想成为宝可梦大师的少年训练家。他与皮卡丘结下深厚羁绊，"
            "一路旅行挑战各地道馆，结识伙伴，在无数对战中不断成长，陪伴了无数观众的童年。"
        ),
        "quote": "\"皮卡丘，就决定是你了！\""
    },
    {
        "id": 12,
        "name": "芙莉莲",
        "name_en": "Frieren",
        "work": "葬送的芙莉莲",
        "work_en": "Frieren: Beyond Journey's End",
        "avatar": "🧙",
        "tags": ["奇幻", "时间", "治愈"],
        "voice_actor": "种崎敦美",
        "personality": "淡漠而温柔、长寿精灵",
        "introduction": (
            "打败魔王后继续旅行的长寿精灵魔法使。对于人类而言短暂的几十年，"
            "对她来说转瞬即逝。她踏上一段重新理解人类、理解\"逝去\"与\"羁绊\"的追忆之旅，"
            "是近年现象级动漫《葬送的芙莉莲》的主角。"
        ),
        "quote": "\"魔王，已经讨伐完成了呢。\""
    },
]

# 1. 获取动漫人物列表（支持按关键词 name / work 过滤）
@router.get("/list")
async def get_anime_list(keyword: str = ""):
    keyword = keyword.strip().lower()
    characters = ANIME_CHARACTERS
    if keyword:
        characters = [
            c for c in characters
            if keyword in c["name"].lower()
            or keyword in c["work"].lower()
            or keyword in c["name_en"].lower()
            or keyword in c["work_en"].lower()
        ]
    # 列表返回精简字段，避免一次性传输过长介绍
    result = [
        {
            "id": c["id"],
            "name": c["name"],
            "name_en": c["name_en"],
            "work": c["work"],
            "avatar": c["avatar"],
            "tags": c["tags"],
        }
        for c in characters
    ]
    return {"success": True, "total": len(result), "characters": result}

# 2. 获取单个动漫人物详情
@router.get("/{character_id}")
async def get_anime_detail(character_id: int):
    for c in ANIME_CHARACTERS:
        if c["id"] == character_id:
            return {"success": True, "character": c}
    raise HTTPException(status_code=404, detail="未找到该动漫人物")
