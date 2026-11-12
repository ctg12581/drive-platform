<!-- src/App.vue -->
<template>
  <div class="app-layout">
    
    <!-- 1. 移动端顶部固定栏 (💡 点击左侧头像现在会瞬间“滑出”侧边抽屉栏) -->
    <header class="mobile-top-bar">
      <div class="avatar-placeholder" @click="isMobileMenuOpen = true" style="cursor: pointer;">
        <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
        <span v-else>{{ authStore.avatar }}</span>
      </div>
      <div class="app-logo">𝕏 DRIVE Space</div>
      <div class="top-action-placeholder" style="width: 32px;"></div>
    </header>

    <!-- 2. 全站核心响应式布局 -->
    <div class="main-container">
      <!-- 左侧边栏导航 (PC 端可见) -->
      <aside class="sidebar">
        <div class="sidebar-logo">𝕏</div>
        <nav class="sidebar-nav">
          <!-- 主页 -->
          <router-link to="/home" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 2.69l5.66 5.58a1 1 0 0 1 .3.71V19a2 2 0 0 1-2 2H13v-6h-2v6H8a2 2 0 0 1-2-2V8.98a1 1 0 0 1 .3-.71z"/></svg>
            </span>
            <span class="text">主页</span>
          </router-link>

          <!-- 搜索 -->
          <router-link to="/search" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z"/></svg>
            </span>
            <span class="text">搜索</span>
          </router-link>

          <!-- 默契度挑战 (仅在 PC 侧边栏常驻) -->
          <router-link to="/quiz" class="sidebar-link" active-class="active">
            <span class="icon" style="color: #db2777;">
              <svg viewBox="0 0 24 24" class="svg-icon" style="fill: currentColor;"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </span>
            <span class="text">默契度挑战</span>
          </router-link>

          <!-- 动漫人物 (💡 新增) -->
          <router-link to="/anime" class="sidebar-link" active-class="active">
            <span class="icon" style="color: #7c3aed;">
              <svg viewBox="0 0 24 24" class="svg-icon" style="fill: currentColor;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8 0-1.42.37-2.74 1.03-3.9L9 12v2a2 2 0 0 0 2 2v1a1 1 0 0 0-1 1v1h2v-2a2 2 0 0 1 2-2l2-2v-1a2 2 0 0 0-2-2h-1V8a2 2 0 0 0-2-2h-.5a2 2 0 0 0-1.2.4L7.5 7.5A8 8 0 0 1 12 4c4.41 0 8 3.59 8 8s-3.59 8-8 8z"/></svg>
            </span>
            <span class="text">动漫人物</span>
          </router-link>

          <!-- DRIVE 人格评测 (💡 新增) -->
          <router-link to="/drive" class="sidebar-link" active-class="active">
            <span class="icon" style="color: #1d9bf0;">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm1.07-7.75-.9.92C12.45 11.1 12 11.5 12 13h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26A1.96 1.96 0 0 0 13 7a2 2 0 1 0-4 0H7a4 4 0 1 1 8 0c0 .88-.36 1.68-.93 2.25z"/></svg>
            </span>
            <span class="text">人格评测</span>
          </router-link>

          <!-- 通知 -->
          <router-link to="/notifications" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M21.163 11.636L19 9.473V6c0-3.309-2.691-6-6-6S7 2.691 7 6v3.473L4.837 11.64c-.21.21-.337.5-.337.803v3.53c0 .553.448 1 1 1h5.182a3.003 3.003 0 0 0 5.636 0h5.182c.552 0 1-.447 1-1v-3.53c0-.303-.127-.593-.337-.807zM13 19a1.002 1.002 0 0 1-1-1h2c0 .552-.448 1-1 1zm7-3H6v-3.111l1.837-1.836A1 1 0 0 0 8.163 11V6c0-2.206 1.794-4 4-4s4 1.794 4 4v5a1 1 0 0 0 .326.713L20 12.889V16z"/></svg>
            </span>
            <span class="nav-text-container">
              <span class="text">通知</span>
              <span v-if="chatStore.pendingRequestsCount > 0" class="global-unread-badge">
                {{ chatStore.pendingRequestsCount }}
              </span>
            </span>
          </router-link>

          <!-- 聊天 -->
          <router-link to="/chat" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/></svg>
            </span>
            <span class="nav-text-container">
              <span class="text">聊天</span>
              <span v-if="chatStore.totalUnreadCount > 0" class="global-unread-badge">
                {{ chatStore.totalUnreadCount }}
              </span>
            </span>
          </router-link>

          <!-- 个人资料 -->
          <router-link to="/auth" class="sidebar-link" active-class="active">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            </span>
            <span class="text">个人资料</span>
          </router-link>

          <!-- PC 发帖大按钮 -->
          <button v-if="authStore.isLoggedIn" @click="showComposeModal = true" class="sidebar-post-btn">
            发 帖
          </button>
        </nav>

        <!-- 侧边栏底部个人名片 -->
        <div v-if="authStore.isLoggedIn" class="sidebar-profile">
          <div class="profile-avatar">
            <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
            <span v-else>{{ authStore.avatar }}</span>
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ authStore.nickname || authStore.username }}</div>
            <div class="profile-handle" style="font-size: 0.8rem; color: var(--x-text-gray);">@{{ authStore.username }}</div>
          </div>
        </div>
      </aside>

      <!-- 中间主内容流 -->
      <main class="content-area">
        <router-view />
      </main>

      <!-- 右侧推荐区 -->
      <aside class="right-panel">
        <div class="trends-box">
          <h3>𝕏 推荐话题</h3>
          <div class="trend-item">
            <span class="trend-category">科技 · 推荐</span>
            <span class="trend-tag">#DRIVE模型架构</span>
            <span class="trend-meta">52.8k 评测</span>
          </div>
          <div class="trend-item">
            <span class="trend-category">社交 · 热议</span>
            <span class="trend-tag">#X.com经典架构</span>
            <span class="trend-meta">18.2k 正在讨论</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- 移动端右下角悬浮发帖按钮 (只有在 '/home' 路由下才显示) -->
    <button v-if="authStore.isLoggedIn && route.path === '/home'" @click="showComposeModal = true" class="mobile-fab-btn">
      <svg viewBox="0 0 24 24" class="svg-inline" style="width: 24px; height: 24px; fill: white;"><path d="M23 3c-6.62-.1-10.38 2.421-13.05 6.03C7.29 12.61 6 17.331 6 22h2c0-1.007.07-2.012.19-3H12c4.1 0 7.48-3.082 7.94-7.054C22.79.137 23 0 23 0zm-7 11.054c-2.45 0-4.44-1.59-4.44-4.041 0-2.451 1.99-4.441 4.44-4.441 2.451 0 4.441 1.99 4.441 4.441 0 2.451-1.99 4.041-4.441 4.041zM2.5 15h3V13h-3v-3h-2v3h-3v2h3v3h2v-3z"/></svg>
    </button>

    <!-- 💡 3. 移动端底部固底导航栏 (彻底精简为最干净的 4 维大导航，移除了默契) -->
    <nav class="mobile-bottom-bar">
      <!-- 主页 -->
      <router-link to="/home" class="bottom-link" active-class="active">
        <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 2.69l5.66 5.58a1 1 0 0 1 .3.71V19a2 2 0 0 1-2 2H13v-6h-2v6H8a2 2 0 0 1-2-2V8.98a1 1 0 0 1 .3-.71z"/></svg>
      </router-link>
      <!-- 搜索 -->
      <router-link to="/search" class="bottom-link" active-class="active">
        <svg viewBox="0 0 24 24" class="svg-icon"><path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z"/></svg>
      </router-link>
      <!-- 通知 (带红点) -->
      <router-link to="/notifications" class="bottom-link" active-class="active">
        <div class="bottom-icon-container">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M21.163 11.636L19 9.473V6c0-3.309-2.691-6-6-6S7 2.691 7 6v3.473L4.837 11.64c-.21.21-.337.5-.337.803v3.53c0 .553.448 1 1 1h5.182a3.003 3.003 0 0 0 5.636 0h5.182c.552 0 1-.447 1-1v-3.53c0-.303-.127-.593-.337-.807zM13 19a1.002 1.002 0 0 1-1-1h2c0 .552-.448 1-1 1zm7-3H6v-3.111l1.837-1.836A1 1 0 0 0 8.163 11V6c0-2.206 1.794-4 4-4s4 1.794 4 4v5a1 1 0 0 0 .326.713L20 12.889V16z"/></svg>
          <span v-if="chatStore.pendingRequestsCount > 0" class="global-unread-badge-mobile">
            {{ chatStore.pendingRequestsCount }}
          </span>
        </div>
      </router-link>
      <!-- 聊天 (带红点) -->
      <router-link to="/chat" class="bottom-link" active-class="active">
        <div class="bottom-icon-container">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/></svg>
          <span v-if="chatStore.totalUnreadCount > 0" class="global-unread-badge-mobile">
            {{ chatStore.totalUnreadCount }}
          </span>
        </div>
      </router-link>
    </nav>

    <!-- 💡 4. 新增：移动端极简 𝕏 侧边滑出抽屉菜单 (Mobile Slide-out Drawer) -->
    <div v-if="isMobileMenuOpen" class="mobile-drawer-backdrop" @click="isMobileMenuOpen = false">
      <!-- 阻止事件冒泡，防止点击抽屉内也触发关闭 -->
      <div class="mobile-drawer" @click.stop>
        <div class="drawer-header">
          <div class="drawer-avatar">
            <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
            <span v-else>{{ authStore.avatar }}</span>
          </div>
          <div class="drawer-user-info">
            <div class="drawer-nickname">{{ authStore.nickname || authStore.username }}</div>
            <div class="drawer-handle">@{{ authStore.username }}</div>
          </div>
        </div>

        <!-- 抽屉导航链接 -->
        <nav class="drawer-nav">
          <!-- 💡 默契度入口移植到此 -->
          <router-link to="/quiz" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="icon" style="color: #db2777;">
              <svg viewBox="0 0 24 24" class="svg-icon-drawer"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </span>
            <span class="text">默契度挑战</span>
          </router-link>

          <!-- 💡 动漫人物入口移植到此 -->
          <router-link to="/anime" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="icon" style="color: #7c3aed;">
              <svg viewBox="0 0 24 24" class="svg-icon-drawer"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8 0-1.42.37-2.74 1.03-3.9L9 12v2a2 2 0 0 0 2 2v1a1 1 0 0 0-1 1v1h2v-2a2 2 0 0 1 2-2l2-2v-1a2 2 0 0 0-2-2h-1V8a2 2 0 0 0-2-2h-.5a2 2 0 0 0-1.2.4L7.5 7.5A8 8 0 0 1 12 4c4.41 0 8 3.59 8 8s-3.59 8-8 8z"/></svg>
            </span>
            <span class="text">动漫人物</span>
          </router-link>

          <!-- 💡 DRIVE 人格评测入口 (移动端抽屉) -->
          <router-link to="/drive" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="icon" style="color: #1d9bf0;">
              <svg viewBox="0 0 24 24" class="svg-icon-drawer"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm1.07-7.75-.9.92C12.45 11.1 12 11.5 12 13h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26A1.96 1.96 0 0 0 13 7a2 2 0 1 0-4 0H7a4 4 0 1 1 8 0c0 .88-.36 1.68-.93 2.25z"/></svg>
            </span>
            <span class="text">人格评测</span>
          </router-link>

          <!-- 个人资料/设置 -->
          <router-link to="/auth" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="icon">
              <svg viewBox="0 0 24 24" class="svg-icon-drawer"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            </span>
            <span class="text">个人资料</span>
          </router-link>
        </nav>

        <div class="drawer-footer">
          <button @click="handleLogout" class="x-btn-danger-pill" style="height: 38px; width: 100%;">
            退出登录
          </button>
        </div>
      </div>
    </div>

    <!-- 全局发帖大模态弹窗 -->
    <div v-if="showComposeModal" class="modal-backdrop" @click.self="closeComposeModal">
      <div class="modal-card compose-modal-card">
        <div class="compose-modal-header">
          <button class="modal-close-btn" @click="closeComposeModal">
            <svg viewBox="0 0 24 24" class="svg-inline"><path d="M10.59 12L4.54 5.96l1.42-1.42L12 10.59l6.04-6.05 1.42 1.42L13.41 12l6.05 6.04-1.42 1.42L12 13.41l-6.04 6.05-1.42-1.42L10.59 12z"/></svg>
          </button>
        </div>
        <div class="global-compose-body">
          <div class="profile-avatar compose-avatar">
            <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
            <span v-else>{{ authStore.avatar }}</span>
          </div>
          <div class="compose-content-area">
            <textarea v-model="globalPostContent" placeholder="有什么新鲜事吗？" class="global-textarea" rows="4" maxlength="280"></textarea>
            <div class="compose-divider"></div>
            <div class="compose-footer-row">
              <span class="char-counter" :class="{ 'warning-count': globalPostContent.length >= 260 }">
                {{ globalPostContent.length }}/280
              </span>
              <button @click="handleGlobalPublish" class="pill-btn" :disabled="!globalPostContent.trim()">发布</button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { isUrl } from '@drive/shared'
import { useAuthStore } from './store/auth'
import { useChatStore } from './store/chat'
import { useMomentsStore } from './store/home'
import { apiFetch } from './utils/api'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const chatStore = useChatStore()
const momentsStore = useMomentsStore()
const router = useRouter()
const route = useRoute()

// 移动端侧边抽屉控制状态
const isMobileMenuOpen = ref(false)

const showComposeModal = ref(false)
const globalPostContent = ref('')

const handleLogout = () => {
  isMobileMenuOpen.value = false 
  chatStore.disconnectWebSocket()
  authStore.logout()
  router.push('/auth')
}

const closeComposeModal = () => {
  showComposeModal.value = false
  globalPostContent.value = ''
}

const handleGlobalPublish = async () => {
  if (!globalPostContent.value.trim()) return
  try {
    const res = await apiFetch('/moments', {
      method: 'POST',
      body: JSON.stringify({ content: globalPostContent.value.trim() }),
    })
    if (res.ok) {
      globalPostContent.value = ''
      showComposeModal.value = false
      if (route.path !== '/home') {
        await router.push('/home')
      }
      momentsStore.requestRefresh()
    } else {
      const data = await res.json().catch(() => ({}))
      alert(data.detail || '发布失败')
    }
  } catch {
    alert('发布失败')
  }
}

onMounted(() => {
  if (authStore.isLoggedIn) {
    chatStore.connectWebSocket()
  }
})

watch(() => authStore.isLoggedIn, (loggedIn) => {
  if (loggedIn) {
    chatStore.connectWebSocket()
  } else {
    chatStore.disconnectWebSocket()
  }
})
</script>






<style>
/* 𝕏 全局重置样式（移动端自适应） */
:root {
  --x-blue: #1d9bf0;
  --x-bg-hover: rgba(15, 20, 25, 0.1);
  --x-border: #eff3f4;
  --x-text-main: #0f1419;
  --x-text-gray: #536471;
}
body {
  background-color: #ffffff;
  color: var(--x-text-main);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  overflow-y: scroll;
}

.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 响应式布局 */
.main-container {
  display: flex;
  width: 100%;
  max-width: 1250px;
  margin: 0 auto;
  justify-content: center;
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
.avatar-placeholder-link {
  text-decoration: none; color: inherit; display: flex; align-items: center;
}
.avatar-placeholder {
  width: 32px; height: 32px;
  background: #ffffff; border: 1px solid var(--x-border);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; overflow: hidden;
}
.app-logo { font-weight: 900; font-size: 1.25rem; }

/* PC侧边栏 */
.sidebar {
  display: none;
  width: 275px;
  height: 100vh;
  position: fixed;
  left: calc((100% - 1250px) / 2);
  top: 0;
  border-right: 1px solid var(--x-border);
  padding: 12px 20px;
  box-sizing: border-box;
}
.sidebar-logo {
  font-size: 1.75rem; font-weight: 900; margin-bottom: 24px; padding-left: 12px;
}
.sidebar-nav { display: flex; flex-direction: column; gap: 8px; }
.sidebar-link {
  display: flex; align-items: center; gap: 16px;
  padding: 12px; text-decoration: none; color: var(--x-text-main);
  font-size: 1.25rem; font-weight: 500; border-radius: 9999px;
  transition: background 0.2s;
}
.sidebar-link:hover { background: var(--x-bg-hover); }
.sidebar-link.active { font-weight: bold; }
.sidebar-link .svg-icon { width: 26px; height: 26px; }

/* PC侧边栏发帖大丸子按钮 */
.sidebar-post-btn {
  background: var(--x-blue);
  color: white;
  border: none;
  font-size: 1.15rem;
  font-weight: bold;
  width: 90%;
  height: 48px;
  border-radius: 9999px;
  cursor: pointer;
  margin-top: 16px;
  transition: background 0.2s;
  display: block;
}
.sidebar-post-btn:hover {
  background: #1a8cd8;
}

/* PC侧边栏底部名片 */
.sidebar-profile {
  position: absolute; bottom: 20px; left: 20px; right: 20px;
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: 9999px; cursor: pointer;
}
.sidebar-profile:hover { background: var(--x-bg-hover); }
.profile-avatar {
  width: 40px; height: 40px; background: #ffffff; border: 1px solid var(--x-border);
  border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; overflow: hidden;
}
.profile-info { display: flex; flex-direction: column; text-align: left; }
.profile-name { font-weight: bold; font-size: 0.95rem; }

/* 响应式主体区 */
.content-area {
  flex: 1;
  max-width: 100%;
  box-sizing: border-box;
  padding-top: 53px; 
  padding-bottom: 53px; 
}

/* 右侧面板 (PC端) */
.right-panel {
  display: none;
  width: 350px;
  padding: 12px 20px;
  box-sizing: border-box;
}
.trends-box {
  background: #f7f9fa; border-radius: 16px; padding: 16px; margin-top: 12px;
}
.trends-box h3 { margin: 0 0 16px 0; font-size: 1.25rem; font-weight: 800; }
.trend-item { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; cursor: pointer; }
.trend-category { font-size: 0.8rem; color: var(--x-text-gray); }
.trend-tag { font-weight: bold; font-size: 0.95rem; }
.trend-meta { font-size: 0.8rem; color: var(--x-text-gray); }

/* 移动端漂浮发帖按钮 (FAB) */
.mobile-fab-btn {
  position: fixed;
  bottom: 70px;
  right: 16px;
  width: 50px;
  height: 50px;
  background: var(--x-blue);
  border: none;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 101;
  display: flex;
}

/* 移动端底部固底栏 */
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
.bottom-link.active { color: var(--x-blue); }
.bottom-link .svg-icon, .mobile-top-bar .svg-icon { width: 26px; height: 26px; fill: currentColor; }

/* 侧边栏及移动底栏未读数红点 */
.nav-text-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.global-unread-badge {
  background: #ef4444;
  color: white;
  font-size: 0.75rem;
  font-weight: bold;
  min-width: 18px;
  height: 18px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  box-sizing: border-box;
}
.bottom-icon-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.global-unread-badge-mobile {
  position: absolute;
  top: -6px;
  right: -8px;
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  font-weight: bold;
  min-width: 16px;
  height: 16px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
  box-sizing: border-box;
}

/* 𝕏 经典发帖大模态弹窗样式 */
.modal-backdrop {
  position: fixed; top: 0; bottom: 0; left: 0; right: 0;
  background: rgba(0, 0, 0, 0.4); display: flex; align-items: flex-start; justify-content: center;
  z-index: 1000;
  padding-top: 50px;
}
@media (min-width: 768px) {
  .modal-backdrop { padding-top: 100px; }
}
.compose-modal-card {
  width: 100%; max-width: 520px; background: white; border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.15); border: 1px solid var(--x-border);
  overflow: hidden; display: flex; flex-direction: column;
}
.compose-modal-header {
  display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--x-border);
}
.modal-close-btn {
  background: transparent; border: none; cursor: pointer; color: var(--x-text-main); display: flex; align-items: center; padding: 4px; border-radius: 50%; transition: background 0.2s;
}
.modal-close-btn:hover { background: var(--x-bg-hover); }
.modal-close-btn .svg-inline { width: 20px; height: 20px; fill: currentColor; }

.global-compose-body { display: flex; gap: 14px; padding: 16px; }
.compose-avatar { width: 42px; height: 42px; border-radius: 50%; border: 1px solid var(--x-border); overflow: hidden; display: flex; align-items: center; justify-content: center; background: white; font-weight: bold; }
.compose-content-area { flex: 1; display: flex; flex-direction: column; }
.global-textarea { width: 100%; border: none; resize: none; font-size: 1.1rem; line-height: 1.5; color: var(--x-text-main); outline: none; background: transparent; padding: 4px 0; font-family: inherit; }
.global-textarea::placeholder { color: var(--x-text-gray); }
.compose-divider { height: 1px; background: var(--x-border); margin: 12px 0; }
.compose-footer-row { display: flex; justify-content: space-between; align-items: center; }
.char-counter { font-size: 0.8rem; color: var(--x-text-gray); font-weight: 500; }
.char-counter.warning-count { color: #ef4444; }
.pill-btn { background: var(--x-blue); color: white; border: none; padding: 0 20px; height: 36px; border-radius: 9999px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
.pill-btn:hover { background: #1a8cd8; }
.pill-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.avatar-img-el {
  width: 100%; height: 100%; object-fit: cover; border-radius: 50%;
}

/* 响应式适配 */
@media (min-width: 768px) {
  .mobile-top-bar, .mobile-bottom-bar, .mobile-fab-btn { display: none !important; }
  .sidebar { display: block; }
  .content-area {
    margin-left: 275px; 
    max-width: 600px;
    border-right: 1px solid var(--x-border);
    padding-top: 12px;
    padding-bottom: 12px;
  }
}
@media (min-width: 1095px) {
  .right-panel { display: block; }
}
/* 💡 新增：移动端顶部头像无下划线高亮链接 */
.avatar-placeholder-link {
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
}

/* 💡 新增：移动端极简 𝕏 侧边抽屉菜单样式 (适配手机触控体验) */
.mobile-drawer-backdrop {
  position: fixed; top: 0; bottom: 0; left: 0; right: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  justify-content: flex-start; /* 靠左对齐 */
}
/* 电脑端强制隐藏该抽屉 */
@media (min-width: 768px) {
  .mobile-drawer-backdrop { display: none !important; }
}

.mobile-drawer {
  width: 280px;
  height: 100%;
  background: #ffffff;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  padding: 20px 16px;
  box-sizing: border-box;
  /* 𝕏 经典滑出阻尼弹性动画 */
  animation: slide-right 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.12);
}
@keyframes slide-right {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(0); }
}

/* 抽屉头部用户信息区 */
.drawer-header {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--x-border);
  text-align: left;
}
.drawer-avatar {
  width: 48px; height: 48px; background: #ffffff; border: 1px solid var(--x-border);
  border-radius: 50%; display: flex; align-items: center; justify-content: center; 
  font-weight: bold; overflow: hidden; margin-bottom: 12px; font-size: 1.4rem;
}
.drawer-user-info { display: flex; flex-direction: column; }
.drawer-nickname { font-weight: bold; font-size: 1.1rem; color: var(--x-text-main); }
.drawer-handle { font-size: 0.9rem; color: var(--x-text-gray); margin-top: 1px; }

/* 抽屉操作链接 */
.drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px 0;
  flex: 1;
}
.drawer-link {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 12px;
  text-decoration: none;
  color: var(--x-text-main);
  font-size: 1.1rem;
  font-weight: bold;
  border-radius: 8px;
  transition: background 0.15s;
  text-align: left;
}
.drawer-link:hover { background: var(--x-bg-hover); }
.drawer-link.active { color: var(--x-blue); background: var(--x-bg-hover); }
.svg-icon-drawer { width: 22px; height: 22px; fill: currentColor; }

/* 抽屉底部安全注销 */
.drawer-footer {
  border-top: 1px solid var(--x-border);
  padding-top: 16px;
}
</style>