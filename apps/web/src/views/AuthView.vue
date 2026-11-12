<!-- src/views/AuthView.vue · 小红书风格登录 / 个人主页 -->
<template>
  <div class="auth-wrapper">
    <!-- 未登录：登录 / 注册 -->
    <div v-if="!authStore.isLoggedIn" class="auth-card">
      <div class="brand-logo-large">
        <svg viewBox="0 0 100 100" class="drive-logo-svg">
          <defs>
            <linearGradient id="drive-grad-simple" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
              <stop stop-color="#ff2442"/>
              <stop offset="1" stop-color="#ff7a90"/>
            </linearGradient>
          </defs>
          <path d="M 25,15 H 50 C 70,15 85,30 85,50 C 85,70 70,85 50,85 H 25 Z"
                stroke="url(#drive-grad-simple)" stroke-width="10" stroke-linejoin="round" stroke-linecap="round" fill="none"/>
          <path d="M 42,34 L 66,50 L 42,66 Z" fill="url(#drive-grad-simple)" />
        </svg>
      </div>

      <h2 class="auth-title">{{ authMode === 'login' ? '登录 DRIVE Space' : '注册 DRIVE Space' }}</h2>
      <p class="auth-sub">记录生活 · 分享灵感 · 遇见同好</p>

      <form class="form-container" @submit.prevent="handleSubmit">
        <div class="x-input-group">
          <input type="text" v-model="form.username" required placeholder="用户名 (@username)">
        </div>
        <div class="x-input-group">
          <input type="password" v-model="form.password" required placeholder="输入密码">
        </div>
        <button type="submit" class="xhs-btn-primary auth-submit">
          {{ authMode === 'login' ? '登录' : '创建账户' }}
        </button>
      </form>
      <p class="toggle-text">
        <span v-if="authMode === 'login'">还没有账号？<a @click.prevent="authMode = 'register'">立即注册</a></span>
        <span v-else>已有账号？<a @click.prevent="authMode = 'login'">前往登录</a></span>
      </p>
    </div>

    <!-- 已登录：个人主页 -->
    <div v-else class="profile-page-container">
      <!-- 顶部封面 -->
      <div class="profile-banner">
        <div class="profile-avatar-big">
          <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
          <span v-else>{{ authStore.avatar }}</span>
        </div>
      </div>

      <div class="profile-meta">
        <div class="profile-name-row">
          <h2 class="profile-nickname">{{ authStore.nickname || authStore.username }}</h2>
          <div class="profile-actions-row">
            <button @click="showEditModal = true" class="btn-edit">编辑资料</button>
            <button @click="handleLogout" class="btn-logout">退出</button>
          </div>
        </div>
        <p class="profile-handle">@{{ authStore.username }}</p>
        <div class="profile-stats">
          <div class="stat"><b>{{ myPosts.length }}</b><span>笔记</span></div>
          <div class="stat"><b>—</b><span>关注</span></div>
          <div class="stat"><b>—</b><span>粉丝</span></div>
        </div>
      </div>

      <!-- 我的笔记 -->
      <div class="my-notes-section">
        <h3 class="section-head">TA 的笔记</h3>

        <div v-if="loading" class="notes-grid">
          <div v-for="i in 2" :key="i" class="note-skeleton">
            <div class="note-skeleton-cover"></div>
            <div class="note-skeleton-line"></div>
          </div>
        </div>

        <div v-else>
          <div v-if="myPosts.length === 0" class="xhs-empty" style="padding:44px 20px;">
            你还没有发布过笔记<br />去首页记录这一刻吧 ✨
          </div>
          <div v-else class="notes-grid">
            <article v-for="(post, idx) in myPosts" :key="post.id" class="note-card">
              <div class="note-cover" :style="noteCoverStyle(post, idx)">
                <img v-if="noteImage(post)" :src="noteImage(post)" class="cover-img" loading="lazy" alt="" @error="onCoverError" />
                <div v-else class="cover-text">
                  <span class="cover-text-inner">{{ post.content }}</span>
                </div>
              </div>
              <div class="note-body">
                <h4 class="note-title">{{ post.content }}</h4>
                <div class="note-foot">
                  <span class="note-time">{{ formatLocalTime(post.time) }}</span>
                  <span class="note-like">♡ {{ noteLikes(post, idx) }}</span>
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>

      <!-- 编辑资料弹窗 -->
      <div v-if="showEditModal" class="modal-backdrop" @click.self="showEditModal = false">
        <div class="modal-card edit-modal">
          <button class="modal-close" @click="showEditModal = false">✕</button>
          <h3 class="edit-title">编辑个人资料</h3>
          <form @submit.prevent="updateProfile">
            <div class="edit-group">
              <label class="edit-label">昵称</label>
              <input type="text" v-model="profileForm.nickname" placeholder="设置个性昵称" required class="edit-input">
            </div>
            <div class="edit-group">
              <label class="edit-label">头像（Emoji 或图片链接）</label>
              <input type="text" v-model="profileForm.avatar_url" placeholder="自定义头像…" required class="edit-input">
            </div>
            <div class="emoji-picker">
              <span v-for="emoji in ['🚀','🐱','🦊','🎮','🦄','🐧','🌸','🐼']" :key="emoji"
                    @click="profileForm.avatar_url = emoji" class="emoji-item">
                {{ emoji }}
              </span>
            </div>
            <button type="submit" class="xhs-btn-primary edit-submit">保存修改</button>
          </form>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { isUrl } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import { useChatStore } from '../store/chat'
import { useRouter } from 'vue-router'
import { formatLocalTime } from '../utils/date'
import { apiFetch, API_BASE } from '../utils/api'
import { invalidateCache } from '../utils/cache'

const authStore = useAuthStore()
const chatStore = useChatStore()
const router = useRouter()

const authMode = ref('login')
const showEditModal = ref(false)
const loading = ref(true)

const form = reactive({ username: '', password: '' })

const profileForm = reactive({
  nickname: authStore.nickname || authStore.username,
  avatar_url: authStore.avatar || '👤'
})

const myPosts = ref([])

// 我的笔记卡片视觉（确定性）
const GRADS = [
  'linear-gradient(135deg,#ffd8e2 0%,#fff0f4 100%)',
  'linear-gradient(135deg,#d9e9ff 0%,#eef5ff 100%)',
  'linear-gradient(135deg,#dcf7e3 0%,#f1fdf4 100%)',
  'linear-gradient(135deg,#fff0d1 0%,#fff9ed 100%)',
  'linear-gradient(135deg,#e8e0ff 0%,#f6f1ff 100%)',
  'linear-gradient(135deg,#ffe0d1 0%,#fff2eb 100%)',
]
const EMOJIS = ['🌿', '☕', '📷', '🍜', '🎨', '🏃', '📚', '✈️', '🎧', '🌷']
const noteHash = (s = '') => {
  let h = 2166136261
  const str = String(s)
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}
const noteCoverStyle = (p, idx) => {
  const h = noteHash(`${p.id}|${p.content}|${idx}`)
  return { background: GRADS[h % GRADS.length], height: 140 + ((h >>> 4) % 5) * 14 + 'px' }
}
const noteEmoji = (p, idx) => EMOJIS[noteHash(`${p.id}|${p.content}|${idx}`) % EMOJIS.length]
const noteImage = (p) => (p && p.image && isUrl(p.image) ? p.image : '')
const onCoverError = (e) => { if (e && e.target) e.target.style.display = 'none' }
const noteLikes = (p, idx) => {
  const n = 30 + (noteHash(`${p.id}|${p.content}`) % 6800)
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`
}

onMounted(() => {
  if (authStore.isLoggedIn) {
    fetchProfile()
    fetchMyPosts()
  }
})

const fetchProfile = async () => {
  try {
    const res = await apiFetch(`/auth/profile/${authStore.username}`)
    const data = await res.json()
    if (res.ok) {
      profileForm.nickname = data.nickname || authStore.username
      profileForm.avatar_url = data.avatar || '👤'
      authStore.updateProfileState(profileForm.nickname, profileForm.avatar_url)
    }
  } catch (err) {
    console.error('获取个人资料失败', err)
  }
}

const fetchMyPosts = async () => {
  loading.value = true
  try {
    const res = await apiFetch(`/moments/user/${authStore.username}`)
    const data = await res.json()
    if (res.ok) {
      myPosts.value = data.moments || []
    }
  } catch (err) {
    console.error('获取个人动态失败', err)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  const endpoint = authMode.value === 'login' ? '/auth/login' : '/auth/register'
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    const data = await res.json()
    if (res.ok) {
      if (authMode.value === 'register') {
        alert(data.message || '注册成功！')
        authMode.value = 'login'
      } else {
        authStore.setLogin(data.access_token, form.username, form.username, '👤')
        await fetchProfile()
        await fetchMyPosts()
        router.push('/home')
      }
    } else {
      alert(data.detail || '验证失败，请重新确认')
    }
  } catch {
    alert('网络故障')
  }
}

const updateProfile = async () => {
  try {
    const res = await apiFetch('/auth/profile', {
      method: 'POST',
      body: JSON.stringify({
        nickname: profileForm.nickname.trim(),
        avatar_url: profileForm.avatar_url.trim()
      })
    })
    if (res.ok) {
      authStore.updateProfileState(profileForm.nickname.trim(), profileForm.avatar_url.trim())
      showEditModal.value = false
      invalidateCache(`profile:${authStore.username}`)
      fetchMyPosts()
    }
  } catch (err) {
    console.error(err)
    alert('修改资料失败')
  }
}

const handleLogout = () => {
  chatStore.disconnectWebSocket()
  authStore.logout()
  router.push('/auth')
}
</script>

<style scoped>
.auth-wrapper { width: 100%; background: #fff; min-height: calc(100vh - var(--app-top) - var(--app-bottom)); }

/* ============ 登录 ============ */
.auth-card {
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
  padding: 56px 24px 40px;
  text-align: center;
}
.brand-logo-large { width: 74px; height: 74px; margin: 0 auto 20px; }
.brand-logo-large .drive-logo-svg { width: 100%; height: 100%; }
.auth-title { font-size: 1.5rem; font-weight: 900; margin: 0 0 6px; color: var(--xhs-text); letter-spacing: -0.4px; }
.auth-sub { font-size: 0.86rem; color: var(--xhs-text-3); margin: 0 0 28px; }

.form-container { width: 100%; }
.x-input-group { margin-bottom: 14px; }
.x-input-group input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border: 1.5px solid transparent;
  border-radius: 14px;
  background: #f4f4f6;
  color: var(--xhs-text);
  box-sizing: border-box;
  font-size: 0.94rem;
  outline: none;
  transition: all 0.16s;
}
.x-input-group input:focus { border-color: var(--xhs-red); background: #fff; box-shadow: 0 0 0 3px rgba(255, 36, 66, 0.1); }
.x-input-group input::placeholder { color: var(--xhs-text-3); }
.auth-submit { width: 100%; height: 46px; margin-top: 8px; font-size: 1rem; }
.toggle-text { font-size: 0.88rem; color: var(--xhs-text-3); margin-top: 22px; }
.toggle-text a { color: var(--xhs-red); text-decoration: none; font-weight: 700; cursor: pointer; margin-left: 4px; }

/* ============ 个人主页 ============ */
.profile-page-container { width: 100%; }
.profile-banner {
  height: 118px;
  background: linear-gradient(135deg, #ffd9e1 0%, #ffeef2 45%, #fff 100%);
  position: relative;
}
.profile-avatar-big {
  position: absolute;
  left: 20px;
  bottom: -36px;
  width: 82px;
  height: 82px;
  background: #fff;
  border-radius: 50%;
  font-size: 2.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 0 0 4px #fff, 0 6px 18px rgba(0, 0, 0, 0.12);
}
.avatar-img-el { width: 100%; height: 100%; object-fit: cover; }

.profile-meta { padding: 46px 20px 16px; }
.profile-name-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.profile-nickname { margin: 0; font-size: 1.35rem; font-weight: 900; color: var(--xhs-text); }
.profile-actions-row { display: flex; gap: 8px; }
.btn-edit {
  background: #fff;
  color: var(--xhs-text);
  border: 1px solid var(--xhs-line);
  font-weight: 700;
  font-size: 0.8rem;
  padding: 0 16px;
  height: 32px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-edit:hover { background: #fafafa; }
.btn-logout {
  background: var(--xhs-red-soft);
  color: var(--xhs-red);
  border: none;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 0 16px;
  height: 32px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
}
.btn-logout:hover { background: #ffe1e6; }
.profile-handle { margin: 6px 0 14px; color: var(--xhs-text-3); font-size: 0.86rem; }
.profile-stats { display: flex; gap: 26px; }
.stat { display: flex; align-items: baseline; gap: 5px; font-size: 0.82rem; color: var(--xhs-text-3); }
.stat b { font-size: 1rem; font-weight: 800; color: var(--xhs-text); }

/* 我的笔记 */
.my-notes-section { padding: 4px 10px 24px; border-top: 1px solid var(--xhs-line); }
.section-head { font-size: 0.98rem; font-weight: 800; margin: 16px 6px 10px; }
.notes-grid { column-count: 2; column-gap: 10px; }
.note-card {
  break-inside: avoid;
  margin: 0 0 10px;
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #f2f2f4;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  animation: xhs-fade-up 0.3s ease both;
}
.note-cover { position: relative; width: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.cover-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.cover-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px 12px;
  overflow: hidden;
}
.cover-text-inner {
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 1.5;
  color: #3a2b30;
  text-align: center;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.cover-emoji { font-size: 2.2rem; filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.12)); }
.note-body { padding: 9px 10px 11px; }
.note-title {
  margin: 0;
  font-size: 0.84rem;
  font-weight: 700;
  line-height: 1.42;
  color: var(--xhs-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}
.note-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.note-time { font-size: 0.68rem; color: var(--xhs-text-3); }
.note-like { font-size: 0.7rem; color: var(--xhs-text-3); }

/* 骨架 */
.notes-grid .note-skeleton, .note-skeleton {
  break-inside: avoid;
  margin-bottom: 10px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #f2f2f4;
}
.note-skeleton-cover { height: 150px; background: #f0f1f3; animation: xhs-pulse 1.4s infinite; }
.note-skeleton-line { height: 10px; margin: 10px; border-radius: 5px; background: #f0f1f3; }

/* 编辑弹窗 */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.modal-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 22px;
  padding: 26px 22px 22px;
  position: relative;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
  animation: xhs-fade-up 0.22s ease;
  text-align: left;
}
.modal-close {
  position: absolute;
  top: 14px;
  right: 16px;
  background: transparent;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  color: var(--xhs-text-3);
}
.edit-title { margin: 0 0 20px; font-size: 1.15rem; font-weight: 800; text-align: center; }
.edit-group { margin-bottom: 14px; }
.edit-label { display: block; font-size: 0.78rem; color: var(--xhs-text-3); font-weight: 700; margin-bottom: 6px; }
.edit-input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border: 1.5px solid transparent;
  border-radius: 12px;
  background: #f4f4f6;
  color: var(--xhs-text);
  box-sizing: border-box;
  font-size: 0.92rem;
  outline: none;
}
.edit-input:focus { border-color: var(--xhs-red); background: #fff; }
.emoji-picker { display: flex; justify-content: space-between; margin: 4px 0 18px; padding: 0 2px; }
.emoji-item { font-size: 1.5rem; cursor: pointer; transition: transform 0.1s; }
.emoji-item:hover { transform: scale(1.2); }
.edit-submit { width: 100%; }
</style>
