# app/main.py
"""DRIVE Space 多模块平台 FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.db import close_pool, init_global_tables, init_pool
from app.modules.admin.router import router as admin_router
from app.modules.anime.router import router as anime_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.drive.router import router as drive_router
from app.modules.moments.router import router as moments_router
from app.modules.quiz.router import router as quiz_router
from app.modules.search.router import router as search_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时创建连接池并初始化数据库表结构，退出时关闭连接池。"""
    await init_pool()
    await init_global_tables()
    yield
    await close_pool()


app = FastAPI(title="DRIVE Space Multi-Feature Platform", lifespan=lifespan)

# 内置允许跨域的前端来源，可通过环境变量 FRONTEND_ORIGINS 追加
DEFAULT_ORIGINS = [
    "https://ctg12581.github.io",
    "https://drive-model-frontend.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


def get_cors_origins() -> list[str]:
    extra = [origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()]
    # dict.fromkeys 去重且保持顺序
    return list(dict.fromkeys([*DEFAULT_ORIGINS, *extra]))


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 压缩 JSON 响应，减小列表/动态等大响应体的传输体积
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(auth_router)
app.include_router(drive_router)
app.include_router(chat_router)
app.include_router(moments_router)
app.include_router(search_router)
app.include_router(quiz_router)
app.include_router(admin_router)
app.include_router(anime_router)


@app.get("/")
async def root():
    return {"message": "Welcome to DRIVE Multi-Feature Space Platform API!"}


@app.get("/api/ping", tags=["保活接口"])
async def ping():
    return {"status": "ok"}
