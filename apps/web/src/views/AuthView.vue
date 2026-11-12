<!-- src/views/AuthView.vue (除了 <style scoped> 外的完整无缺版代码) -->
<template>
  <div class="auth-wrapper">
    <!-- 未登录状态：展示极简 𝕏 登录/注册表单 -->
    <div v-if="!authStore.isLoggedIn" class="auth-card">
      <div class="brand-logo-large">
        <svg viewBox="0 0 100 100" class="drive-logo-svg">
          <defs>
            <linearGradient id="drive-grad-simple" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
              <stop stop-color="#1d9bf0"/>
              <stop offset="1" stop-color="#4f46e5"/>
            </linearGradient>
          </defs>
          <path d="M 25,15 H 50 C 70,15 85,30 85,50 C 85,70 70,85 50,85 H 25 Z" 
                stroke="url(#drive-grad-simple)" stroke-width="10" stroke-linejoin="round" stroke-linecap="round" fill="none"/>
          <path d="M 42,34 L 66,50 L 42,66 Z" fill="url(#drive-grad-simple)" />
        </svg>
      </div>

      <div class="form-container">
        <h2 class="auth-title">{{ authMode === 'login' ? '登录您的 DRIVE Space' : '立即注册 DRIVE Space' }}</h2>
        <form @submit.prevent="handleSubmit">
          <div class="x-input-group">
            <input type="text" v-model="form.username" required placeholder="用户名 (@username)">
          </div>
          <div class="x-input-group">
            <input type="password" v-model="form.password" required placeholder="输入密码">
          </div>
          <button type="submit" class="x-btn-dark">
            {{ authMode === 'login' ? '登录' : '创建账户' }}
          </button>
        </form>
        <p class="toggle-text">
          <span v-if="authMode === 'login'">还没有账号？ <a @click.prevent="authMode = 'register'">立即创建账户</a></span>
          <span v-else>已有账号？ <a @click.prevent="authMode = 'login'">前往登录</a></span>
        </p>
      </div>
    </div>

    <!-- 已登录状态：自适应升级为 𝕏 经典个人主页 (Profile Page) -->
    <div v-else class="profile-page-container">
      
      <!-- 主页头部名片卡 -->
      <div class="profile-hero-card">
        <div class="profile-avatar-big">
          <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
          <span v-else>{{ authStore.avatar }}</span>
        </div>
        <div class="profile-meta-info">
          <h2 class="profile-nickname">{{ authStore.nickname || authStore.username }}</h2>
          <p class="profile-handle">@{{ authStore.username }}</p>
          <div class="profile-actions-row">
            <!-- 弹出修改名片表单 -->
            <button @click="showEditModal = true" class="x-btn-pill-light">编辑个人资料</button>
            <button @click="handleLogout" class="x-btn-danger-pill">退出登录</button>
          </div>
          
 
        </div>
      </div>

      <!-- 我的历史动态流 (支持 SWR 0ms 瞬间还原) -->
      <div class="my-timeline">
        <h3 class="timeline-title">我的动态 ({{ myPosts.length }})</h3>
        
        <!-- 骨架屏占位 -->
        <div v-if="loading" class="skeleton-container" style="padding-top: 10px;">
          <div class="skeleton-card" v-for="i in 2" :key="i">
            <div class="skeleton-avatar"></div>
            <div class="skeleton-info">
              <div class="skeleton-line short"></div>
              <div class="skeleton-line long"></div>
            </div>
          </div>
        </div>

        <div v-else class="my-posts-list">
          <div v-if="myPosts.length === 0" class="no-posts-hint">
            您还没有发表过任何动态，去主页发一条新鲜事吧！
          </div>
          <div v-for="post in myPosts" :key="post.id" class="my-tweet-card">
            <div class="my-tweet-avatar">
              <img v-if="isUrl(authStore.avatar)" :src="authStore.avatar" class="avatar-img-el" />
              <span v-else>{{ authStore.avatar }}</span>
            </div>
            <div class="my-tweet-main">
              <div class="my-tweet-header">
                <span class="my-tweet-author">{{ authStore.nickname }}</span>
                <span class="my-tweet-handle">@{{ authStore.username }} · {{ formatLocalTime(post.time) }}</span>
              </div>
              <div class="my-tweet-content">{{ post.content }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 💡 1. 弹出模态：编辑个人名片弹窗 -->
      <div v-if="showEditModal" class="modal-backdrop" @click.self="showEditModal = false">
        <div class="modal-card" style="max-width: 400px; padding: 24px; text-align: left;">
          <button class="modal-close" @click="showEditModal = false">✕</button>
          <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 800; text-align: center; margin-bottom: 20px;">编辑个人资料</h3>
          <form @submit.prevent="updateProfile">
            <div class="x-input-group-edit">
              <label class="edit-label">我的昵称</label>
              <input type="text" v-model="profileForm.nickname" placeholder="设置个性昵称" required class="x-input-field">
            </div>
            <div class="x-input-group-edit">
              <label class="edit-label">我的头像 (Emoji 或图片链接)</label>
              <input type="text" v-model="profileForm.avatar_url" placeholder="自定义头像..." required class="x-input-field">
            </div>
            <!-- 快捷推荐 Emoji -->
            <div class="emoji-picker">
              <span v-for="emoji in ['🚀','🐱','🦊','🎮','🦄','🐧','🌸','🐼']" :key="emoji" 
                    @click="profileForm.avatar_url = emoji" class="emoji-item">
                {{ emoji }}
              </span>
            </div>
            <button type="submit" class="x-btn-dark" style="background: var(--x-blue); color: white; height: 40px; margin-top: 20px;">
              保存修改
            </button>
          </form>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../store/auth'
import { useChatStore } from '../store/chat'  // 💡 用于安全登出时切断 WebSocket
import { useRouter } from 'vue-router'
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:3000'
const authStore = useAuthStore()
const chatStore = useChatStore()
const router = useRouter()

const authMode = ref('login')
const showEditModal = ref(false)
const loading = ref(true)

// 登录注册表单
const form = reactive({ username: '', password: '' })

// 个人名片表单（瞬间读取缓存，0ms秒开）
const profileForm = reactive({
  nickname: authStore.nickname || authStore.username,
  avatar_url: authStore.avatar || '👤'
})

// 我的历史动态与题库变量
const myPosts = ref([])
const bankQuestions = ref([])
const myAnswers = reactive({}) // 绑定出题答案：{ "1": "A", "2": "C" }

onMounted(() => {
  if (authStore.isLoggedIn) {
    fetchProfile()
    fetchMyPosts()
  }
})

// 获取个人名片
const fetchProfile = async () => {
  try {
    const res = await apiFetch(`/auth/profile/${authStore.username}`)
    const data = await res.json()
    if (res.ok) {
      profileForm.nickname = data.nickname || authStore.username
      profileForm.avatar_url = data.avatar || '👤'
      // 实时同步写入全局状态银行，触发全站侧边栏、顶栏瞬间更新
      authStore.updateProfileState(profileForm.nickname, profileForm.avatar_url)
    }
  } catch (err) {
    console.error('获取个人资料失败', err)
  }
}

// 获取我发过的历史动态
const fetchMyPosts = async () => {
  loading.value = true
  try {
    const res = await apiFetch(`/moments/user/${authStore.username}`)
    const data = await res.json()
    if (res.ok) {
      myPosts.value = data.moments
    }
  } catch (err) {
    console.error('获取个人动态失败', err)
  } finally {
    loading.value = false
  }
}

// 登录注册
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

// 更新个人资料
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
      fetchMyPosts() // 重新刷一遍我的帖子，让帖子里的头像昵称也实时同步
    }
  } catch (err) {
    console.error(err)
    alert('修改资料失败')
  }
}

// 安全注销
const handleLogout = () => {
  chatStore.disconnectWebSocket()
  authStore.logout()
  router.push('/auth')
}


const isUrl = (text) => {
  if (!text) return false
  return text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')
}
</script>




<style scoped>
/* 𝕏 经典个人主页专属排版 */
.auth-wrapper { width: 100%; position: relative; }
.auth-card { width: 100%; max-width: 360px; text-align: center; margin: 40px auto; }
.brand-logo-large { width: 80px; height: 80px; margin: 0 auto 24px auto; }
.brand-logo-large .drive-logo-svg { width: 100%; height: 100%; }
.auth-title { font-size: 1.5rem; font-weight: 800; margin-bottom: 24px; letter-spacing: -0.5px; background: linear-gradient(135deg, #1d9bf0, #4f46e5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.x-input-group { margin-bottom: 16px; }
.x-input-group input {
  width: 100%; height: 46px; padding: 0 16px; border: 1px solid var(--x-border); border-radius: 8px;
  background: transparent; color: var(--x-text-main); box-sizing: border-box; font-size: 0.95rem; outline: none;
}
.x-input-group input:focus { border-color: var(--x-blue); }

.x-btn-dark {
  width: 100%; height: 44px; background: #0f1419; color: #ffffff; border: none; border-radius: 9999px; font-weight: bold; font-size: 1rem; cursor: pointer; transition: background 0.2s; margin-top: 10px;
}
.x-btn-dark:hover { background: #272c30; }
.toggle-text { font-size: 0.9rem; color: var(--x-text-gray); margin-top: 20px; }
.toggle-text a { color: var(--x-blue); text-decoration: none; font-weight: bold; cursor: pointer; }

/* 🌟 已登录：个人主页排版 */
.profile-page-container { width: 100%; }
.profile-hero-card {
  display: flex; flex-direction: column; align-items: center; padding: 24px 16px; border-bottom: 1px solid var(--x-border); text-align: center;
}
@media (min-width: 500px) {
  .profile-hero-card { flex-direction: row; text-align: left; gap: 24px; }
}
.profile-avatar-big {
  width: 80px; height: 80px; background: #ffffff; border: 1px solid var(--x-border); border-radius: 50%; font-size: 2.5rem; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 12px;
}
@media (min-width: 500px) { .profile-avatar-big { margin-bottom: 0; } }

.profile-meta-info { flex: 1; display: flex; flex-direction: column; }
.profile-nickname { margin: 0; font-size: 1.5rem; font-weight: 800; color: var(--x-text-main); }
.profile-handle { margin: 4px 0 16px 0; color: var(--x-text-gray); font-size: 1rem; }
.profile-actions-row { display: flex; gap: 12px; justify-content: center; }
@media (min-width: 500px) { .profile-actions-row { justify-content: flex-start; } }

/* 扁平化丸子按钮 */
.x-btn-pill-light {
  background: transparent; color: var(--x-text-main); border: 1px solid var(--x-border); font-weight: bold; font-size: 0.85rem; padding: 0 16px; height: 34px; border-radius: 9999px; cursor: pointer; transition: background 0.15s;
}
.x-btn-pill-light:hover { background: var(--x-bg-hover); }

.x-btn-danger-pill {
  background: transparent; color: #ef4444; border: 1px solid #fca5a5; font-weight: bold; font-size: 0.85rem; padding: 0 16px; height: 34px; border-radius: 9999px; cursor: pointer; transition: all 0.15s;
}
.x-btn-danger-pill:hover { background: #fee2e2; border-color: #ef4444; }

/* 个人时间轴 */
.my-timeline { width: 100%; }
.timeline-title { font-size: 1.1rem; font-weight: 800; padding: 16px 16px 8px 16px; margin: 0; text-align: left; }
.no-posts-hint { text-align: center; color: var(--x-text-gray); font-size: 0.95rem; padding: 40px; }

/* 我的推文卡片 */
.my-tweet-card { display: flex; padding: 16px; border-bottom: 1px solid var(--x-border); gap: 12px; }
.my-tweet-avatar {
  width: 40px; height: 40px; border-radius: 50%; background: #ffffff; border: 1px solid var(--x-border); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; overflow: hidden;
}
.my-tweet-main { flex: 1; text-align: left; }
.my-tweet-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.my-tweet-author { font-weight: bold; font-size: 0.95rem; color: var(--x-text-main); }
.my-tweet-handle { color: var(--x-text-gray); font-size: 0.85rem; }
.my-tweet-content { font-size: 0.95rem; line-height: 1.5; word-wrap: break-word; color: var(--x-text-main); }

/* 编辑弹窗表单组 */
.x-input-group-edit { margin-bottom: 16px; text-align: left;}
.x-input-field {
  width: 100%; height: 46px; padding: 0 16px; border: 1px solid var(--x-border); border-radius: 8px; background: transparent; color: var(--x-text-main); box-sizing: border-box; font-size: 0.95rem; outline: none;
}
.x-input-field:focus { border-color: var(--x-blue); }
.edit-label { display: block; font-size: 0.8rem; color: var(--x-text-gray); font-weight: bold; margin-bottom: 6px; padding-left: 2px; }

.emoji-picker { display: flex; justify-content: space-between; margin-bottom: 16px; padding: 0 4px; }
.emoji-item { font-size: 1.5rem; cursor: pointer; transition: transform 0.1s; }
.emoji-item:hover { transform: scale(1.2); }

/* 弹窗遮罩与卡片 */
.modal-backdrop { position: fixed; top: 0; bottom: 0; left: 0; right: 0; background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { width: 90%; max-width: 450px; background: white; border-radius: 20px; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; position: relative; box-shadow: 0 8px 30px rgba(0,0,0,0.15); }
.modal-close { position: absolute; top: 16px; right: 16px; background: transparent; border: none; font-size: 1.25rem; font-weight: bold; cursor: pointer; color: var(--x-text-gray); }

/* 骨架屏 */
@keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
.skeleton-container { display: flex; flex-direction: column; }
.skeleton-card { display: flex; gap: 12px; padding: 16px; border-bottom: 1px solid var(--x-border); animation: pulse 1.5s infinite; }
.skeleton-avatar { width: 40px; height: 40px; border-radius: 50%; background: #eff3f4; }
.skeleton-info { flex: 1; display: flex; flex-direction: column; gap: 8px; justify-content: center; }
.skeleton-line { height: 11px; background: #eff3f4; border-radius: 4px; }
.skeleton-line.short { width: 25%; }
.skeleton-line.long { width: 85%; }
</style>