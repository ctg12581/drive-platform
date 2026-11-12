# DRIVE Platform

DRIVE 人格评估平台 —— 用户端、管理后台与 FastAPI 后端统一仓库（pnpm monorepo）。

## 目录结构

```
apps/web        # 用户端 Vue 3 SPA
apps/admin      # 管理后台 Vue 3 SPA
services/api    # FastAPI + PostgreSQL 后端
packages/shared # 前端共享工具 @drive/shared（请求封装、时间、缓存等）
docs/           # DRIVE 模型理论、部署与审查文档
```

## 快速开始

前端（仓库根目录）：

```bash
pnpm install
pnpm dev:web     # 用户端 http://localhost:5173
pnpm dev:admin   # 管理后台
pnpm build       # 构建两个前端
pnpm test:shared # 共享包单测
```

后端：

```bash
cd services/api
python -m venv venv && .\venv\Scripts\activate   # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                            # 填写数据库/密钥等配置
python server.py                                  # http://127.0.0.1:3000 ，文档 /docs
```

## 环境变量

- 后端：`services/api/.env`，参考 [.env.example](services/api/.env.example)，**切勿提交真实密钥**。
  必填 `DATABASE_URL`、`JWT_SECRET`；首次部署设 `ADMIN_PASSWORD` 以创建初始管理员。
- 前端：`apps/web/.env.*`、`apps/admin/.env.production`（仅含 API 地址）。

## 部署

完整步骤见 [docs/DEPLOY.md](docs/DEPLOY.md)。

- **前端**：push 到 `main` 后由 [deploy-pages.yml](.github/workflows/deploy-pages.yml) 自动构建并部署到 GitHub Pages。
- **后端**：由 [render.yaml](render.yaml) 部署到 Render，push 到 `main` 自动更新。
- 生产地址：用户端 <https://ctg12581.github.io/drive-platform/> · 后台 <https://ctg12581.github.io/drive-platform/admin/> · API <https://drive-model-backend.onrender.com>

## 说明

- 首次启动后端会自动建表/迁移（含 `users.is_admin`、`created_at` 时区、索引）。升级前先备份数据库。
- 聊天 WebSocket 需携带 Token（`?token=`）；管理员由数据库 `is_admin` 判定。
- 本地 `.env` 曾出现真实 Neon / R2 / JWT 凭据，请尽快在控制台轮换。
