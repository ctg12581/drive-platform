# DRIVE Platform Monorepo

DRIVE 人格评估平台 —— 用户端、管理后台与 FastAPI 后端统一仓库。

## 目录结构

```
drive-platform/
├─ apps/
│  ├─ web/                 # 用户端 Vue 3 SPA（原 drive-model-frontend）
│  └─ admin/               # 管理后台 Vue 3 SPA（原 drive-admin-frontend）
├─ services/
│  └─ api/                 # FastAPI 后端（原 drive-model-backend）
├─ packages/
│  └─ shared/              # 前端共享工具（@drive/shared：请求封装、时间格式化）
├─ docs/
│  ├─ DRIVE.md             # DRIVE 模型理论文档
│  └─ 项目合并可行性分析.md
├─ pnpm-workspace.yaml
├─ package.json            # workspace 根
└─ README.md
```

## 快速开始

### 前端（pnpm workspace）

```bash
# 在仓库根目录
pnpm install

pnpm dev:web      # 用户端，默认 http://localhost:5173
pnpm dev:admin    # 管理后台
pnpm build:web
pnpm build:admin
```

> 两个前端仍各自独立构建、独立部署（GitHub Pages / Vercel 等）。

### 后端（FastAPI）

```bash
cd services/api
python -m venv venv
# Windows: .\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # 然后填写真实配置
python server.py         # 默认 http://127.0.0.1:3000 ，接口文档 /docs
```

## 环境变量

- 后端：`services/api/.env`（参考 `services/api/.env.example`），**不要提交真实密钥**。
- 用户端：`apps/web/.env.development`（本地）/ `.env.production`（线上）。
- 后台：`apps/admin/.env`（`VITE_API_BASE`）。

## 部署相关

- 用户端 `apps/web/vite.config.js` 中 `base: 'drive-model-frontend'` 用于 GitHub Pages 子路径部署；若更换部署路径需同步修改。
- 后端 CORS 白名单在 `services/api/app/main.py` 的 `origins` 中维护，新增前端域名需追加。

## 版本控制说明

本仓库为合并后的**单一新仓库**。原三个项目各自的 `.git` 目录已备份到仓库外的 `../_git_backup/`（`drive-model-backend.git`、`drive-model-frontend.git`），如需找回历史可从此处恢复。

## 待办 / 后续演进

1. 将 `apps/web`、`apps/admin` 中重复的 `apiFetch`、`formatLocalTime` 改为引用 `@drive/shared`。
2. 如需进一步收敛，可评估「方案 B：后台并入用户端 `/admin` 路由，单构建」。
3. 轮换曾在本地 `.env` 出现过的 Neon / JWT / R2 凭据。
