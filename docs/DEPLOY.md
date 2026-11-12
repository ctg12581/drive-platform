# 部署指南

> 目标拓扑：**前端（用户端 + 管理后台）→ GitHub Pages；后端 → Render**。
> 仓库：`ctg12581/drive-platform`（若实际仓库名不同，替换文中的 `drive-platform`）。

## 0. 地址一览

| 角色 | 地址 |
|---|---|
| 后端 API | https://drive-model-backend.onrender.com |
| 用户端 | https://ctg12581.github.io/drive-platform/ |
| 管理后台 | https://ctg12581.github.io/drive-platform/admin/ |
| Render 控制台 | https://dashboard.render.com/web/srv-d8ugqmok1i2s73eum0jg |

---

## 1. GitHub 仓库准备

1. 将本地 `drive-platform` 推到 GitHub 的 `main` 分支：
   ```bash
   git remote add origin https://github.com/ctg12581/drive-platform.git
   git push -u origin main
   ```
2. **Settings → Actions → General → Workflow permissions**：选择 **Read and write permissions**（部署需要推 `gh-pages` 分支）。
3. **Settings → Pages**：Source 选择 **Deploy from a branch** → 分支 `gh-pages` → 目录 `/ (root)`。

## 2. 前端部署（GitHub Pages）

工作流：[.github/workflows/deploy-pages.yml](../.github/workflows/deploy-pages.yml)

- 触发：push 到 `main`（涉及 `apps/**`、`packages/**`、锁文件等工作流文件）。
- 步骤：`pnpm install --frozen-lockfile` → 构建 `drive-model-frontend` 与 `drive-admin-frontend` → 把 admin 产物复制进 `apps/web/dist/admin` → 部署 `apps/web/dist` 到 `gh-pages`。
- 两个前端都用相对 `base: './'` + hash 路由，因此 `/admin/` 子路径不需要额外路由重写。
- `.nojekyll` 已随构建产出，避免 GitHub Pages 的 Jekyll 处理。

> 一个 GitHub 仓库只能有一个 Pages 站点，所以 admin 放在同一站点的 `/admin/` 子路径。如果后台要单独上 Vercel，请告知，可拆成两份部署配置。

## 3. 后端部署（Render）

服务：`drive-model-backend`（Service ID `srv-d8ugqmok1i2s73eum0jg`）。

> ⚠️ 当前 Render 连接的是旧仓库 `ctg12581/drive-model-backend`；合并后的代码在本 monorepo 的 `services/api`。**需要把服务的 Repository 改为 `ctg12581/drive-platform`**。

Settings 对齐：

| 项 | 值 |
|---|---|
| Repository | `ctg12581/drive-platform` |
| Branch | `main` |
| Root Directory | `services/api` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python server.py` |
| Health Check Path | `/api/ping` |

环境变量（Environment）：

| Key | 说明 |
|---|---|
| `PYTHON_VERSION` | `3.12.6` |
| `DATABASE_URL` | PostgreSQL 连接串（Neon 等） |
| `JWT_SECRET` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 可选，默认 `525600` |
| `FRONTEND_ORIGINS` | 可选，额外允许的前端来源，逗号分隔 |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Cloudflare R2 凭据 |
| `R2_BUCKET_NAME` | `drive-space` |
| `R2_PUBLIC_URL` | R2 公开访问域名 |

也可以让 Render 直接用根目录的 [render.yaml](../render.yaml) 作为 Blueprint 管理该服务。

验证：
```bash
curl https://drive-model-backend.onrender.com/api/ping
# {"status":"ok"}
```

## 4. 上线后验证清单

- [ ] `GET /api/ping` 返回 `{"status":"ok"}`
- [ ] 用户端首页可打开，静态资源 200（浏览器控制台无 404）
- [ ] 注册 / 登录成功（确认请求打到 `drive-model-backend.onrender.com`）
- [ ] 管理后台 `https://ctg12581.github.io/drive-platform/admin/` 可登录并加载数据
- [ ] 浏览器无 CORS 报错（否则把对应域名加进 `FRONTEND_ORIGINS`）
- [ ] 聊天 WebSocket 连接成功（`wss://drive-model-backend.onrender.com`）
- [ ] 图片上传可用（需 R2 配置正确）

## 5. 常见问题

| 现象 | 排查 |
|---|---|
| Render 构建找不到 `requirements.txt` | Root Directory 是否为 `services/api` |
| 页面白屏 / 资源 404 | 确认使用 `base: './'` 构建，且部署的是 `apps/web/dist` |
| 后台请求打到 `127.0.0.1:3000` | CI 是否读取了 `apps/admin/.env.production`（该文件需提交） |
| 浏览器 CORS 报错 | 后端 `FRONTEND_ORIGINS` / `DEFAULT_ORIGINS` 是否包含该前端 origin |
| Render 端口错误 | `server.py` 已读取 `PORT` 环境变量，无需硬编码 |

## 6. 回滚

- 前端：`gh-pages` 分支历史即历史部署，可回退该分支。
- 后端：Render 控制台 Deploys 列表选择上一个成功版本重新部署。
