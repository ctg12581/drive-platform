# app/main.py 鐨勬渶椤堕儴

from fastapi import FastAPI
# 馃挕 1. 纭繚瀵煎叆浜?CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware 
from app.core.db import init_global_tables

from app.modules.auth.router import router as auth_router
from app.modules.drive.router import router as drive_router
from app.modules.chat.router import router as chat_router
from app.modules.moments.router import router as moments_router
from app.modules.search.router import router as search_router
from app.modules.quiz.router import router as quiz_router
from app.modules.admin.router import router as admin_router
from app.modules.anime.router import router as anime_router

app = FastAPI(title="DRIVE Space Multi-Feature Platform")

# 馃挕 2. 鏍稿績淇敼锛氭槑纭寚瀹氬厑璁歌法鍩熻闂殑鍚堟硶鍓嶇鍩熷悕鐧藉悕鍗曪紙褰诲簳閬垮厤褰?allow_credentials=True 鏃朵娇鐢?"*" 瀵艰嚧鐨勬嫤鎴垨宕╂簝锛?
origins = [
    "https://ctg12581.github.io",                # 鐢ㄦ埛绔嚎涓婂煙鍚?
    "https://drive-model-frontend.vercel.app",  # 鐢ㄦ埛绔?Vercel 鍩熷悕
    "http://localhost:5173",                    # 馃挕 鏈湴寮€鍙戝父鐢ㄧ鍙?
    "http://127.0.0.1:5173",
    "http://localhost:5174",                    # 馃挕 澶囩敤鏈湴寮€鍙戠鍙?
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 馃挕 缁戝畾鎸囧畾鐨勭櫧鍚嶅崟鍩熷悕
    allow_credentials=True,      # 鍏佽鎼哄甫 Cookie / 璇佷功楠岃瘉
    allow_methods=["*"],         # 鍏佽鎵€鏈?HTTP 璇锋眰鏂规硶 (GET, POST, OPTIONS 绛?
    allow_headers=["*"],         # 鍏佽鎵€鏈夎嚜瀹氫箟 Request Headers (鍖呮嫭 Authorization)
)

# 鍚姩寤鸿〃
@app.on_event("startup")
async def startup_event():
    init_global_tables()

# 鎸傝浇璺敱...
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

@app.get("/api/ping", tags=["淇濇椿鎺ュ彛"])
async def ping():
    return {"status": "ok"}