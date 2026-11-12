# server.py
import os
import uvicorn
from dotenv import load_dotenv

# 本地调试时，加载 .env 环境变量
load_dotenv()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    # 载入 app/main.py 下的 app 实例
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)