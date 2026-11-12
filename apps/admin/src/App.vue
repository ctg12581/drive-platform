<!-- src/App.vue -->
<template>
  <div class="app-layout">

    <!-- 未登录：仅渲染登录页 (/login) -->
    <router-view v-if="!authStore.isLoggedIn" />

    <!-- 已登录：完整管理员后台骨架 -->
    <div v-else class="admin-wrapper">
      <!-- 移动端顶部固定栏 (在 >=768px 时自动隐藏) -->
      <header class="mobile-top-bar">
        <div class="avatar-placeholder">👑</div>
        <div class="app-logo">𝕏 Admin</div>
        <div class="top-action-placeholder" style="width: 32px;"></div>
      </header>

      <!-- 左侧极客黑色侧边栏 -->
      <aside class="sidebar">
        <div class="sidebar-logo">𝕏 Admin</div>
        <nav class="sidebar-nav">
          <!-- 1. 系统看板 -->
          <router-link to="/dashboard" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14H7v-7h3v7zm4 0h-3V7h3v10zm4 0h-3v-4h3v4z"/></svg>
            </span>
            <span class="text">系统大盘</span>
          </router-link>

          <!-- 2. 题库管理 -->
          <router-link to="/questions" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M22 10.51l-4.57-1.12L16.31 4.8c-.28-.68-.81-.68-1.09 0l-1.12 4.59L9.53 10.51c-.68.28-.68.81 0 1.09l4.57 1.12 1.12 4.59c.28.68.81.68 1.09 0l1.12-4.59 4.57-1.12c.68-.28.68-.81 0-1.09zM8.36 17.51l-1.91-.47-.47-1.91c-.12-.48-.48-.48-.6 0l-.47 1.91-1.91.47c-.48.12-.48.48 0 .6l1.91.47.47 1.91c.12.48.48.48.6 0l.47-1.91 1.91-.47c.48-.12.48-.48 0-.6zm3-11.51l-.95-.23-.23-.95c-.06-.24-.24-.24-.3 0l-.23.95-.95.23c-.24.06-.24.24 0 .3l.95.23.23.95c.06.24.24.24.3 0l.23-.95.95-.23c.24-.06.24-.24 0-.3z"/></svg>
            </span>
            <span class="text">题库管理</span>
          </router-link>

          <!-- 3. 用户活跃监控 -->
          <router-link to="/users" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            </span>
            <span class="text">用户监控</span>
          </router-link>
        </nav>

        <!-- 侧边栏底部个人名片 + 退出 -->
        <div class="sidebar-profile">
          <div class="profile-avatar">👑</div>
          <div class="profile-info">
            <span class="profile-name">系统管理员</span>
            <span class="profile-handle" style="font-size: 0.8rem; color: #8899a6;">@admin</span>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </aside>

      <!-- 右侧全屏操作工作区 -->
      <main class="content-area">
        <router-view />
      </main>

      <!-- 移动端底部固底导航栏 -->
      <nav class="mobile-bottom-bar">
        <router-link to="/dashboard" class="bottom-link" active-class="active">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14H7v-7h3v7zm4 0h-3V7h3v10zm4 0h-3v-4h3v4z"/></svg>
        </router-link>
        <router-link to="/questions" class="bottom-link" active-class="active">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M22 10.51l-4.57-1.12L16.31 4.8c-.28-.68-.81-.68-1.09 0l-1.12 4.59L9.53 10.51c-.68.28-.68.81 0 1.09l4.57 1.12 1.12 4.59c.28.68.81.68 1.09 0l1.12-4.59 4.57-1.12c.68-.28.68-.81 0-1.09zM8.36 17.51l-1.91-.47-.47-1.91c-.12-.48-.48-.48-.6 0l-.47 1.91-1.91.47c-.48.12-.48.48 0 .6l1.91.47.47 1.91c.12.48.48.48.6 0l.47-1.91 1.91-.47c.48-.12.48-.48 0-.6zm3-11.51l-.95-.23-.23-.95c-.06-.24-.24-.24-.3 0l-.23.95-.95.23c-.24.06-.24.24 0 .3l.95.23.23.95c.06.24.24.24.3 0l.23-.95.95-.23c.24-.06.24-.24 0-.3z"/></svg>
        </router-link>
        <router-link to="/users" class="bottom-link" active-class="active">
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
/* 𝕏 后台管理系统全局重置与双栏完美滚动样式 */
html, body, #app {
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  max-width: none !important;  /* 彻底消除 Vite 默认的 1280px 居中限制 */
  text-align: left !important;  /* 彻底消除 Vite 默认的居中对齐 */
  background-color: #ffffff;
  overflow: hidden; /* 💡 保持最外层视口不滚动，防止产生双滚动条 */
}

.app-layout {
  width: 100%;
  height: 100%;
}

/* 经典后台左右双栏骨架 */
.admin-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden; /* 💡 保证侧边栏不参与页面大滚动 */
}

/* 左侧深邃黑色边栏 (PC端默认排版) */
.sidebar {
  display: none;
  width: 250px;
  height: 100%;
  background-color: #0f1419;
  color: #ffffff;
  flex-direction: column;
  padding: 24px 16px;
  box-sizing: border-box;
  border-right: 1px solid #2f3336;
  flex-shrink: 0;
  position: relative;
}
@media (min-width: 768px) {
  .sidebar { display: flex !important; }
}

.sidebar-logo {
  font-size: 1.75rem; font-weight: 900; margin-bottom: 24px; padding-left: 12px;
}
.sidebar-nav { display: flex; flex-direction: column; gap: 8px; }
.sidebar-link {
  display: flex; align-items: center; gap: 16px;
  padding: 12px; text-decoration: none; color: #ffffff;
  font-size: 1.1rem; font-weight: 500; border-radius: 9999px;
  transition: background 0.2s;
}
.sidebar-link:hover { background: var(--x-bg-hover); }
.sidebar-link.active { font-weight: bold; background: var(--x-bg-hover); }
.sidebar-link .svg-icon { width: 26px; height: 26px; fill: currentColor; }

/* 侧边栏底部个人名片 */
.sidebar-profile {
  position: absolute; bottom: 20px; left: 20px; right: 20px;
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: 9999px; cursor: pointer;
}
.sidebar-profile:hover { background: var(--x-bg-hover); }
.profile-avatar {
  width: 40px; height: 40px; background: #ffffff; border: 1px solid #2f3336;
  border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; overflow: hidden;
}
.profile-info { display: flex; flex-direction: column; text-align: left; }
.profile-name { font-weight: bold; font-size: 0.95rem; color: white;}
.profile-handle { font-size: 0.8rem; color: #8899a6; margin-top: 2px; }

/* 退出登录按钮 */
.logout-btn {
  position: absolute; bottom: 78px; left: 20px; right: 20px;
  height: 38px; border-radius: 9999px; border: 1px solid #2f3336;
  background: transparent; color: #ef4444; font-weight: 600; cursor: pointer;
  transition: background 0.2s;
}
.logout-btn:hover { background: #1f2326; }

/* 右侧全屏操作工作区 (已对齐 .content-area 类名，完美支持滑动) */
.content-area {
  flex: 1;
  height: 100%;
  background-color: #ffffff;
  overflow-y: auto !important; /* 💡 开启垂直独立滚动条，彻底解决无法滑动的问题！ */
  box-sizing: border-box;
  padding: 24px 16px;
}
@media (min-width: 768px) {
  .content-area {
    padding: 30px 40px !important; /* PC 端大气内边距 */
  }
}

/* 移动端顶部状态栏 */
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

/* 移动端底部固底导航栏 */
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
.bottom-link .svg-icon, .mobile-top-bar .svg-icon { width: 24px; height: 26px; fill: currentColor; }

/* 📱 双端自适应 */
@media (max-width: 767px) {
  .content-area {
    padding-top: 65px !important;  /* 移动端留出顶部固定状态栏高度 */
    padding-bottom: 65px !important; /* 移动端留出底部固底导航栏高度 */
  }
}
@media (min-width: 768px) {
  .mobile-top-bar, .mobile-bottom-bar { display: none !important; }
}
</style>
