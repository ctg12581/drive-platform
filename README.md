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
│  └─ shared/              # 前端共享工具（@drive/shared）
├─ docs/
│  ├─ DRIVE.md             # DRIVE 模型理论文档
│  └─ 项目合并可行性分析.md
├─ .github/
│  └─ workflows/
│     └─ deploy-pages.yml  # 两个前端 → GitHub Pages
├─ render.yaml             # 后端 Render Blueprint
├─ pnpm-workspace.yaml
├─ package.json            # workspace 根
└─ README.md
```

`@drive/shared` 统一提供两个前端共用的能力，各应用通过 `workspace:*` 依赖与 Vite alias 引用：

- `formatLocalTime` 时间格式化
- `createApiFetch` 请求封装（Token / FormData / 401 拦截）
- `isUrl` / `isImageUrl` 头像与图片判断
- `isTokenExpired` JWT 过期判断
- `readJSON` / `writeJSON` 本地缓存读写

## 快速开始

### 前端（pnpm workspace）

```bash
# 在仓库根目录
pnpm install

pnpm dev:web      # 用户端，默认 http://localhost:5173
pnpm dev:admin    # 管理后台
pnpm build        # 一次构建两个前端
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
- 后台：`apps/admin/.env`（本地，被 gitignore）/ `.env.production`（CI 构建用，已提交）。

## 部署相关

> 完整的逐步操作清单见 [docs/DEPLOY.md](docs/DEPLOY.md)。

### 前端（GitHub Pages）

- 部署由根目录的 [.github/workflows/deploy-pages.yml](.github/workflows/deploy-pages.yml) 自动完成：push 到 `main` 后构建两个前端，并把 `apps/web/dist` 部署到 `gh-pages` 分支。
- 同一个 Pages 站点同时承载两个前端：
  - 用户端：`https://ctg12581.github.io/drive-platform/`
  - 管理后台：`https://ctg12581.github.io/drive-platform/admin/`
- 两个前端均使用相对 `base: './'` 与 hash 路由，因此部署在子路径下无需额外改配置。
- 仓库 Settings → Pages 需把 Source 设为 `gh-pages` 分支（GitHub Actions 推送）。

### 后端（Render）

- 根目录 [render.yaml](render.yaml) 提供了 Render Blueprint；若沿用已有服务 `srv-d8ugqmok1i2s73eum0jg`，在服务设置中手动对齐：
  - Root Directory：`services/api`
  - Build Command：`pip install -r requirements.txt`
  - Start Command：`python server.py`
  - Health Check Path：`/api/ping`
- Render 环境变量至少需要：`DATABASE_URL`、`JWT_SECRET`、`R2_*`；如需额外前端域名，配置 `FRONTEND_ORIGINS`（逗号分隔）。
- 后端 CORS 白名单在 `services/api/app/main.py` 的 `DEFAULT_ORIGINS` 中维护（已包含 `https://ctg12581.github.io`，同源覆盖 web 与 `/admin/` 两个站点）。

### 当前生产地址

| 角色 | 地址 |
|---|---|
| 后端 API | https://drive-model-backend.onrender.com |
| 用户端（GitHub Pages） | https://ctg12581.github.io/drive-platform/ |
| 管理后台（GitHub Pages） | https://ctg12581.github.io/drive-platform/admin/ |
| 旧入口（自动跳转） | https://ctg12581.github.io/drive-model-frontend/ → 新用户端 |

> 若 GitHub 仓库名不是 `drive-platform`，把上面地址中的 `drive-platform` 换成实际仓库名即可（页面路径由仓库名决定，`base: './'` 已兼容）。


## 近期重构说明

- 两个前端的时间格式化、请求封装、头像/图片判断、JWT 判断、本地缓存读写已收敛到 `@drive/shared`，删除两份重复实现。
- 移除未使用的 `counter` store、死代码与重复的工具函数；修复聊天页图片上传缺失 `API_BASE`、WebSocket 重连定时器泄漏、发帖后整页刷新等问题。
- 后端统一使用 `db_cursor` 上下文管理器管理连接/提交/回滚，新增 `app/core/storage.py` 统一 R2 客户端；修复 `app/main.py` 中文乱码并改用 `lifespan`；搜索接口由 N+1 查询改为单次联表查询；DRIVE 评测改为按所选等级计算得分。

## 版本控制说明

本仓库为合并后的**单一新仓库**。原三个项目各自的 `.git` 目录已备份到仓库外的 `../_git_backup/`，如需找回历史可从此处恢复。

## 待办 / 后续演进

1. 轮换曾在本地 `.env` 出现过的 Neon / JWT / R2 凭据。
2. 如需进一步收敛，可评估「方案 B：后台并入用户端 `/admin` 路由，单构建」。
3. 聊天 WebSocket 连接当前以用户名标识在线，建议后续加入 Token 校验以增强安全性。
