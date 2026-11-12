<!-- src/App.vue 移动端单栏布局 · 小红书风格 -->
<template>
  <div class="app-layout">

    <!-- 顶部固定栏：头像 / 品牌 / 通知 -->
    <header class="app-top-bar">
      <button class="top-avatar" @click="isMobileMenuOpen = true" aria-label="菜单">
        <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
        <span v-else>{{ authStore.avatar }}</span>
      </button>

      <div class="app-brand">
        <span class="brand-dot"></span>
        <span class="brand-text">DRIVE</span>
        <span class="brand-sub">Space</span>
      </div>

      <div class="top-actions">
        <button class="top-act" @click="router.push('/search')" aria-label="搜索">
          <svg viewBox="0 0 24 24" class="top-svg"><path d="M10.5 3a7.5 7.5 0 1 1-4.55 13.46l-3.2 3.2a1 1 0 1 1-1.42-1.42l3.2-3.2A7.5 7.5 0 0 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z"/></svg>
        </button>
        <button class="top-bell" @click="router.push('/notifications')" aria-label="通知">
          <svg viewBox="0 0 24 24" class="top-svg"><path d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6.5V11a7 7 0 0 0-5.5-6.84V3.5a1.5 1.5 0 0 0-3 0v.66A7 7 0 0 0 5 11v4.5l-1.6 1.6a1 1 0 0 0 .7 1.7h15.8a1 1 0 0 0 .7-1.7L19 15.5z"/></svg>
          <span v-if="chatStore.pendingRequestsCount > 0" class="top-bell-badge">{{ chatStore.pendingRequestsCount }}</span>
        </button>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main-container">
      <main class="content-area">
        <router-view />
      </main>
    </div>

    <!-- 底部固定导航栏（小红书五宫格） -->
    <nav class="mobile-bottom-bar">
      <router-link to="/home" :class="['bottom-link', { active: isHomeTab }]" aria-label="首页">
        <svg viewBox="0 0 24 24" class="svg-icon"><path d="M11.3 2.6a1 1 0 0 1 1.4 0l8 7.4a1 1 0 0 1 .3.74V20a1.5 1.5 0 0 1-1.5 1.5h-4.4v-6.1h-4.2v6.1H4.5A1.5 1.5 0 0 1 3 20v-9.26a1 1 0 0 1 .3-.74l8-7.4z"/></svg>
        <span class="bottom-label">首页</span>
      </router-link>

      <router-link :to="{ path: '/home', query: { tab: 'rank' } }" :class="['bottom-link', { active: isRankTab }]" aria-label="热榜">
        <svg viewBox="0 0 24 24" class="svg-icon"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z"/></svg>
        <span class="bottom-label">热榜</span>
      </router-link>

      <button class="bottom-publish" @click="openCompose" aria-label="发布">
        <svg viewBox="0 0 24 24" class="publish-svg"><path d="M12 4.5a1.2 1.2 0 0 1 1.2 1.2v5.1h5.1a1.2 1.2 0 1 1 0 2.4h-5.1v5.1a1.2 1.2 0 1 1-2.4 0v-5.1H5.7a1.2 1.2 0 1 1 0-2.4h5.1V5.7A1.2 1.2 0 0 1 12 4.5z"/></svg>
      </button>

      <router-link to="/chat" :class="['bottom-link', { active: route.path === '/chat' }]" aria-label="消息">
        <div class="bottom-icon-container">
          <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 3c5.52 0 10 3.8 10 8.5 0 4.7-4.48 8.5-10 8.5-.9 0-1.78-.1-2.6-.3l-4.2 2.1a.7.7 0 0 1-1-.8l.7-3.1C2.6 16.4 2 14.5 2 11.5 2 6.8 6.48 3 12 3zm-3.4 8.9a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5zm3.4 0a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5zm3.4 0a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5z"/></svg>
          <span v-if="chatStore.totalUnreadCount > 0" class="global-unread-badge-mobile">{{ chatStore.totalUnreadCount }}</span>
        </div>
        <span class="bottom-label">消息</span>
      </router-link>

      <router-link to="/auth" :class="['bottom-link', { active: route.path === '/auth' }]" aria-label="我">
        <svg viewBox="0 0 24 24" class="svg-icon"><path d="M12 12a4.2 4.2 0 1 0 0-8.4 4.2 4.2 0 0 0 0 8.4zm0 2c-3.4 0-7 1.7-7 3.9V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.1c0-2.2-3.6-3.9-7-3.9z"/></svg>
        <span class="bottom-label">我</span>
      </router-link>
    </nav>

    <!-- 侧边滑出抽屉菜单 -->
    <div v-if="isMobileMenuOpen" class="mobile-drawer-backdrop" @click="isMobileMenuOpen = false">
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

        <nav class="drawer-nav">
          <router-link to="/quiz" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="drawer-emoji" style="background:#fff1f3;">💖</span>
            <span class="text">默契度挑战</span>
          </router-link>

          <router-link to="/anime" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="drawer-emoji" style="background:#f2efff;">🎌</span>
            <span class="text">动漫人物</span>
          </router-link>

          <router-link to="/drive" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="drawer-emoji" style="background:#eaf6ff;">🧠</span>
            <span class="text">人格评测</span>
          </router-link>

          <router-link to="/notifications" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="drawer-emoji" style="background:#fff6e8;">🔔</span>
            <span class="text">系统通知</span>
          </router-link>

          <router-link to="/auth" class="drawer-link" active-class="active" @click="isMobileMenuOpen = false">
            <span class="drawer-emoji" style="background:#eef1f5;">👤</span>
            <span class="text">个人主页</span>
          </router-link>
        </nav>

        <div class="drawer-footer">
          <button @click="handleLogout" class="drawer-logout">退出登录</button>
        </div>
      </div>
    </div>

    <!-- 全局发布弹窗 -->
    <div v-if="showComposeModal" class="modal-backdrop" @click.self="closeComposeModal">
      <div class="modal-card compose-modal-card">
        <div class="compose-modal-header">
          <button class="compose-cancel" @click="closeComposeModal">取消</button>
          <span class="compose-title">发布笔记</span>
          <button @click="handleGlobalPublish" class="compose-publish" :disabled="!globalPostContent.trim() || composeUploading">发布</button>
        </div>
        <div class="global-compose-body">
          <div class="compose-content-area">
            <textarea v-model="globalPostContent" placeholder="分享这一刻的新鲜事…" class="global-textarea" rows="4" maxlength="280"></textarea>
            <div class="compose-media-row">
              <input ref="imageInput" type="file" accept="image/*" style="display: none" @change="handleComposeImage" />
              <div v-if="!composeImagePreview" class="media-tile media-add" @click="triggerImagePick">
                <span v-if="!composeUploading">＋</span>
                <span v-else class="media-uploading">上传中…</span>
              </div>
              <div v-else class="media-preview">
                <img :src="composeImagePreview" class="media-preview-img" />
                <button class="media-remove" @click="removeComposeImage" type="button">✕</button>
              </div>
              <span class="compose-hint-inline">添加封面图 · 让笔记更生动</span>
            </div>
            <div class="compose-footer-row">
              <span class="char-counter" :class="{ 'warning-count': globalPostContent.length >= 260 }">{{ globalPostContent.length }}/280</span>
              <span class="compose-hint">图片将作为笔记封面</span>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { isUrl } from '@drive/shared'
import { useAuthStore } from './store/auth'
import { useChatStore } from './store/chat'
import { useMomentsStore } from './store/home'
import { apiFetch } from './utils/api'
import { invalidateCache } from './utils/cache'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const chatStore = useChatStore()
const momentsStore = useMomentsStore()
const router = useRouter()
const route = useRoute()

const isRankTab = computed(() => route.path === '/home' && ['rank', 'rank_intl'].includes(route.query.tab))
const isHomeTab = computed(() => route.path === '/home' && !['rank', 'rank_intl'].includes(route.query.tab))

const isMobileMenuOpen = ref(false)
const showComposeModal = ref(false)
const globalPostContent = ref('')

// 封面图上传
const imageInput = ref(null)
const composeImageUrl = ref('')       // 上传成功后的可访问 URL
const composeImagePreview = ref('')   // 本地即时预览
const composeUploading = ref(false)

const triggerImagePick = () => {
  if (composeUploading.value) return
  imageInput.value && imageInput.value.click()
}

const removeComposeImage = () => {
  composeImageUrl.value = ''
  composeImagePreview.value = ''
  if (imageInput.value) imageInput.value.value = ''
}

const handleComposeImage = async (event) => {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    alert('图片过大，请选择小于 2MB 的图片')
    event.target.value = ''
    return
  }
  composeImagePreview.value = URL.createObjectURL(file)
  composeUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiFetch('/chat/upload', { method: 'POST', body: formData })
    const data = await res.json()
    if (res.ok && data.success && data.url) {
      composeImageUrl.value = data.url
    } else {
      alert(data.detail || '图片上传失败')
      removeComposeImage()
    }
  } catch {
    alert('图片上传失败')
    removeComposeImage()
  } finally {
    composeUploading.value = false
  }
}

const openCompose = () => {
  if (!authStore.isLoggedIn) {
    router.push('/auth')
    return
  }
  showComposeModal.value = true
}

const handleLogout = () => {
  isMobileMenuOpen.value = false
  chatStore.disconnectWebSocket()
  authStore.logout()
  router.push('/auth')
}

const closeComposeModal = () => {
  showComposeModal.value = false
  globalPostContent.value = ''
  removeComposeImage()
}

const handleGlobalPublish = async () => {
  if (!globalPostContent.value.trim() || composeUploading.value) return
  try {
    const res = await apiFetch('/moments', {
      method: 'POST',
      body: JSON.stringify({
        content: globalPostContent.value.trim(),
        image_url: composeImageUrl.value || '',
      }),
    })
    if (res.ok) {
      globalPostContent.value = ''
      showComposeModal.value = false
      removeComposeImage()
      if (route.path !== '/home') {
        await router.push('/home')
      }
      momentsStore.requestRefresh()
      // 自己发了动态，个人主页（含帖子）缓存失效，避免看到旧数据
      invalidateCache(`profile:${authStore.username}`)
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
/* ================= 小红书风格 · 应用外壳 ================= */
body {
  background: var(--xhs-bg);
}
#app {
  min-height: 100vh;
}
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 顶部固定栏 */
.app-top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--app-top);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--xhs-line);
  z-index: 100;
}
.top-avatar {
  width: 34px;
  height: 34px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 1.5px var(--xhs-line);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-weight: 700;
  color: var(--xhs-text);
  cursor: pointer;
}
.app-brand {
  display: flex;
  align-items: baseline;
  gap: 5px;
}
.brand-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--xhs-red);
  align-self: center;
}
.brand-text {
  font-weight: 900;
  font-size: 1.18rem;
  letter-spacing: 0.5px;
  color: var(--xhs-text);
}
.brand-sub {
  font-weight: 700;
  font-size: 0.78rem;
  color: var(--xhs-text-3);
  letter-spacing: 0.3px;
}
.top-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}
.top-act,
.top-bell {
  position: relative;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--xhs-text);
}
.top-svg {
  width: 23px;
  height: 23px;
  fill: currentColor;
}
.top-bell-badge {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 15px;
  height: 15px;
  padding: 0 3px;
  border-radius: var(--xhs-radius-pill);
  background: var(--xhs-red);
  color: #fff;
  font-size: 0.62rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

/* 主容器 */
.main-container {
  display: flex;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  background: #fff;
  min-height: 100vh;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.04);
}
.content-area {
  flex: 1;
  width: 100%;
  box-sizing: border-box;
  padding-top: var(--app-top);
  padding-bottom: var(--app-bottom);
  min-width: 0;
}

/* 底部导航 */
.mobile-bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--app-bottom);
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(14px);
  border-top: 1px solid var(--xhs-line);
  z-index: 100;
  max-width: 640px;
  margin: 0 auto;
}
.bottom-link {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--xhs-text-3);
  text-decoration: none;
  font-weight: 600;
}
.bottom-link .svg-icon {
  width: 24px;
  height: 24px;
  fill: currentColor;
  transition: transform 0.15s;
}
.bottom-label {
  font-size: 0.62rem;
  letter-spacing: 0.3px;
}
.bottom-link.active {
  color: var(--xhs-red);
}
.bottom-link.active .svg-icon {
  transform: translateY(-1px);
}
.bottom-icon-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.global-unread-badge-mobile {
  position: absolute;
  top: -7px;
  right: -9px;
  min-width: 15px;
  height: 15px;
  padding: 0 3px;
  border-radius: var(--xhs-radius-pill);
  background: var(--xhs-red);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: 1.5px solid #fff;
}

/* 中间发布按钮 */
.bottom-publish {
  flex: none;
  width: 56px;
  height: 34px;
  margin: 0 4px;
  border: none;
  border-radius: 12px;
  background: var(--xhs-red);
  box-shadow: 0 6px 16px rgba(255, 36, 66, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.12s, background 0.18s;
}
.bottom-publish:active {
  transform: scale(0.94);
}
.publish-svg {
  width: 22px;
  height: 22px;
  fill: #fff;
}

/* 头像图片 */
.avatar-img-el {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

/* ============ 发布弹窗 ============ */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: 1000;
  padding: 40px 16px;
}
.compose-modal-card {
  width: 100%;
  max-width: 520px;
  background: #fff;
  border-radius: 22px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: xhs-fade-up 0.22s ease;
}
.compose-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--xhs-line);
}
.compose-title {
  font-weight: 800;
  font-size: 1rem;
  color: var(--xhs-text);
}
.compose-cancel {
  background: transparent;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--xhs-text-2);
  cursor: pointer;
}
.compose-publish {
  background: var(--xhs-red);
  color: #fff;
  border: none;
  height: 32px;
  padding: 0 18px;
  border-radius: var(--xhs-radius-pill);
  font-weight: 700;
  font-size: 0.86rem;
  cursor: pointer;
  transition: background 0.18s;
}
.compose-publish:disabled {
  background: #ffc2cb;
  cursor: not-allowed;
}
.global-compose-body {
  padding: 18px;
}
.global-textarea {
  width: 100%;
  border: none;
  resize: none;
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--xhs-text);
  outline: none;
  background: transparent;
  padding: 4px 0;
  font-family: inherit;
}
.global-textarea::placeholder {
  color: var(--xhs-text-3);
}
.compose-media-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 14px 0;
}
.media-tile {
  width: 78px;
  height: 78px;
  border-radius: 12px;
  background: #fafafa;
  border: 1.5px dashed #e4e4e7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: #cfcfd4;
}
.media-add {
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.media-add:hover {
  border-color: var(--xhs-red);
  color: var(--xhs-red);
}
.media-uploading {
  font-size: 0.7rem;
  color: var(--xhs-red);
  font-weight: 700;
}
.media-preview {
  position: relative;
  width: 78px;
  height: 78px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
}
.media-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.media-remove {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 19px;
  height: 19px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  border: none;
  font-size: 0.62rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.compose-hint-inline {
  font-size: 0.76rem;
  color: var(--xhs-text-3);
  flex: 1;
}
.compose-footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--xhs-line);
}
.char-counter {
  font-size: 0.78rem;
  color: var(--xhs-text-3);
  font-weight: 600;
}
.char-counter.warning-count {
  color: var(--xhs-red);
}
.compose-hint {
  font-size: 0.76rem;
  color: var(--xhs-text-3);
}

/* ============ 抽屉菜单 ============ */
.mobile-drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  justify-content: flex-start;
}
.mobile-drawer {
  width: 286px;
  height: 100%;
  background: #fff;
  box-shadow: 6px 0 30px rgba(0, 0, 0, 0.16);
  display: flex;
  flex-direction: column;
  padding: 28px 18px 20px;
  animation: slide-right 0.26s cubic-bezier(0.175, 0.885, 0.32, 1.1);
}
@keyframes slide-right {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(0); }
}
.drawer-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 22px;
  border-bottom: 1px solid var(--xhs-line);
}
.drawer-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 2px var(--xhs-line);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.5rem;
  overflow: hidden;
  flex-shrink: 0;
}
.drawer-user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.drawer-nickname {
  font-weight: 800;
  font-size: 1.1rem;
  color: var(--xhs-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.drawer-handle {
  font-size: 0.84rem;
  color: var(--xhs-text-3);
  margin-top: 3px;
}
.drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 20px 0;
  flex: 1;
}
.drawer-link {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 9px 10px;
  text-decoration: none;
  color: var(--xhs-text);
  font-size: 1rem;
  font-weight: 600;
  border-radius: 12px;
  transition: background 0.15s;
}
.drawer-link:hover {
  background: #fafafa;
}
.drawer-link.active {
  color: var(--xhs-red);
  background: var(--xhs-red-soft);
}
.drawer-emoji {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.05rem;
  flex-shrink: 0;
}
.drawer-footer {
  border-top: 1px solid var(--xhs-line);
  padding-top: 16px;
}
.drawer-logout {
  width: 100%;
  height: 40px;
  border-radius: var(--xhs-radius-pill);
  background: #fff;
  border: 1px solid var(--xhs-red-line);
  color: var(--xhs-red);
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.18s;
}
.drawer-logout:hover {
  background: var(--xhs-red-soft);
}

/* 移动端：主容器铺满 */
@media (max-width: 640px) {
  .main-container {
    box-shadow: none;
  }
  .mobile-bottom-bar {
    max-width: 100%;
  }
}
</style>
