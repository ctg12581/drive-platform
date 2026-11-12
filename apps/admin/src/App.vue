<!-- src/App.vue -->
<template>
  <div class="app-layout">

    <!-- 未登录：仅渲染登录页 (/login) -->
    <router-view v-if="!authStore.isLoggedIn" />

    <!-- 已登录：移动端单栏后台骨架 -->
    <div v-else class="admin-wrapper">
      <header class="mobile-top-bar">
        <div class="avatar-placeholder">👑</div>
        <div class="app-logo">𝕏 Admin</div>
        <button class="logout-btn" @click="handleLogout">退出</button>
      </header>

      <main class="content-area">
        <router-view />
      </main>

      <!-- 底部固定导航栏 -->
      <nav class="mobile-bottom-bar">
        <router-link to="/dashboard" class="bottom-link" active-class="active" aria-label="系统大盘">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14H7v-7h3v7zm4 0h-3V7h3v10zm4 0h-3v-4h3v4z"/></svg>
        </router-link>
        <router-link to="/questions" class="bottom-link" active-class="active" aria-label="题库管理">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M22 10.51l-4.57-1.12L16.31 4.8c-.28-.68-.81-.68-1.09 0l-1.12 4.59L9.53 10.51c-.68.28-.68.81 0 1.09l4.57 1.12 1.12 4.59c.28.68.81.68 1.09 0l1.12-4.59 4.57-1.12c.68-.28.68-.81 0-1.09zM8.36 17.51l-1.91-.47-.47-1.91c-.12-.48-.48-.48-.6 0l-.47 1.91-1.91.47c-.48.12-.48.48 0 .6l1.91.47.47 1.91c.12.48.48.48.6 0l.47-1.91 1.91-.47c.48-.12.48-.48 0-.6zm3-11.51l-.95-.23-.23-.95c-.06-.24-.24-.24-.3 0l-.23.95-.95.23c-.24.06-.24.24 0 .3l.95.23.23.95c.06.24.24.24.3 0l.23-.95.95-.23c.24-.06.24-.24 0-.3z"/></svg>
        </router-link>
        <router-link to="/users" class="bottom-link" active-class="active" aria-label="用户监控">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
        </router-link>
      </nav>
    </div>

  </div>
</template>

<script setup>
import { useAuthStore } from './store/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style>
/* 后台管理系统：移动端单栏布局 */
:root {
  --x-blue: #1d9bf0;
  --x-bg-hover: rgba(15, 20, 25, 0.1);
  --x-border: #eff3f4;
  --x-text-main: #0f1419;
  --x-text-gray: #536471;
}
html, body, #app {
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  max-width: none !important;
  text-align: left !important;
  background-color: #ffffff;
  overflow: hidden;
}

.app-layout {
  width: 100%;
  height: 100%;
}

.admin-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 全屏内容区：为顶部/底部固定栏预留空间 */
.content-area {
  flex: 1;
  width: 100%;
  height: 100%;
  background-color: #ffffff;
  overflow-y: auto !important;
  box-sizing: border-box;
  padding: 65px 16px 65px;
}

/* 顶部固定栏 */
.mobile-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 53px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--x-border);
  padding: 0 16px;
  z-index: 100;
}
.avatar-placeholder {
  width: 32px; height: 32px;
  background: #ffffff; border: 1px solid var(--x-border);
  border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;
}
.app-logo { font-weight: 900; font-size: 1.15rem; color: #1d9bf0; }
.logout-btn {
  height: 30px; padding: 0 14px; border-radius: 9999px;
  border: 1px solid #fca5a5; background: transparent;
  color: #ef4444; font-weight: 600; font-size: 0.8rem; cursor: pointer;
}
.logout-btn:hover { background: #fee2e2; }

/* 底部固定导航栏 */
.mobile-bottom-bar {
  display: flex;
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 53px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--x-border);
  z-index: 100;
}
.bottom-link {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: var(--x-text-main); text-decoration: none;
}
.bottom-link.active { color: #1d9bf0; }
.bottom-link .svg-icon { width: 24px; height: 26px; fill: currentColor; }
</style>
