# server.py
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# 本地调试时加载 services/api/.env（固定相对脚本目录，避免受 CWD 影响）
load_dotenv(Path(__file__).resolve().with_name(".env"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    # 载入 app/main.py 下的 app 实例
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
