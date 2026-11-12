<!-- src/views/SearchView.vue -->
<template>
  <div class="search-container">
    <!-- 𝕏 经典版：顶固高档极简搜索栏 (带 Focus 动态变色) -->
    <div class="search-header">
      <div class="search-input-pill">
        <svg viewBox="0 0 24 24" class="search-icon-svg"><path d="M21.53 20.47l-3.66-3.66C19.195 15.24 20 13.214 20 11c0-4.97-4.03-9-9-9s-9 4.03-9 9 4.03 9 9 9c2.215 0 4.24-.804 5.808-2.13l3.66 3.66c.147.146.34.22.53.22s.385-.073.53-.22c.295-.293.295-.767.002-1.06zM3.5 11c0-4.135 3.365-7.5 7.5-7.5s7.5 3.365 7.5 7.5-3.365 7.5-7.5 7.5-7.5-3.365-7.5-7.5z"/></svg>
        <input type="text" v-model="searchQuery" class="search-input-field" placeholder="搜索用户 @账号 或 个性昵称..." @input="handleSearch">
      </div>
    </div>

    <!-- 搜索结果列表 -->
    <div class="search-results">
      <div v-if="users.length === 0" class="no-results">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">🔍</div>
        <p v-if="searchQuery">没有找到与 “{{ searchQuery }}” 匹配的用户</p>
        <p v-else>输入关键字，在 𝕏 维度空间中寻找新朋友并互粉吧！</p>
      </div>
      
      <div v-else v-for="user in users" :key="user.username" class="user-card" @click="openUserProfile(user.username)">
        <div class="user-card-left">
          <!-- 💡 核心修复：支持 Emoji 和 图片 URL 头像的自适应完美渲染 -->
          <div class="user-avatar-small">
            <img v-if="isUrl(user.avatar)" :src="user.avatar" class="avatar-img" />
            <span v-else-if="user.avatar && user.avatar !== '👤'">{{ user.avatar }}</span>
            <span v-else>{{ user.username[0].toUpperCase() }}</span>
          </div>
          <div class="user-info">
            <div class="user-nickname">{{ user.nickname }}</div>
            <div class="user-username">@{{ user.username }}</div>
          </div>
        </div>
        
        <!-- 关系按钮 (阻止冒泡，点击不触发打开主页) -->
        <div class="user-card-right" @click.stop>
          <button v-if="user.friend_status === 'none'" @click="sendFriendRequest(user.username)" class="btn-follow-pill">
            关注 / 加好友
          </button>
          <span v-else-if="user.friend_status === 'sent'" class="badge-status badge-sent">已申请</span>
          <span v-else-if="user.friend_status === 'received'" class="badge-status badge-received" @click="goToNotifications">待同意</span>
          <span v-else-if="user.friend_status === 'friends'" class="badge-status badge-friends">已互关</span>
        </div>
      </div>
    </div>

    <!-- 个人主页弹窗 (Profile) -->
    <div v-if="activeProfile" class="modal-backdrop" @click.self="activeProfile = null">
      <div class="modal-card">
        <button class="modal-close" @click="activeProfile = null">✕</button>
        <div class="modal-header">
          <div class="modal-avatar-big">
            <img v-if="isUrl(activeProfile.user.avatar)" :src="activeProfile.user.avatar" class="avatar-img" />
            <span v-else-if="activeProfile.user.avatar && activeProfile.user.avatar !== '👤'">{{ activeProfile.user.avatar }}</span>
            <span v-else>{{ activeProfile.user.username[0].toUpperCase() }}</span>
          </div>
          <h2 class="modal-nickname">{{ activeProfile.user.nickname }}</h2>
          <p class="modal-handle">@{{ activeProfile.user.username }}</p>
        </div>
        <div class="modal-body">
          <h3 class="modal-tab-title">TA 的动态 ({{ activeProfile.posts.length }})</h3>
          <div v-if="activeProfile.posts.length === 0" class="no-posts-hint">TA 还没有发布过任何动态。</div>
          <div v-for="p in activeProfile.posts" :key="p.id" class="modal-tweet">
            <div class="modal-tweet-time">{{ formatLocalTime(p.time) }}</div>
            <div class="modal-tweet-content">{{ p.content }}</div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from '../utils/api'
import { useRouter } from 'vue-router'
import { formatLocalTime } from '../utils/date'

const router = useRouter()
const searchQuery = ref('')
const users = ref([])
const activeProfile = ref(null)

let debounceTimer = null

// 模糊搜索
const handleSearch = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (!searchQuery.value.trim()) {
    users.value = []
    return
  }
  debounceTimer = setTimeout(async () => {
    try {
      const res = await apiFetch(`/search/users?q=${encodeURIComponent(searchQuery.value.trim())}`)
      const data = await res.json()
      if (res.ok) {
        users.value = data.users
      }
    } catch (err) {
      console.error('搜索异常:', err)
    }
  }, 350)
}

// 提交好友申请
const sendFriendRequest = async (targetUsername) => {
  try {
    const res = await apiFetch('/chat/add-friend', {
      method: 'POST',
      body: JSON.stringify({ friend_username: targetUsername })
    })
    const data = await res.json()
    if (res.ok) {
      alert(data.message || '请求已发送')
      // 实时修改本地列表状态，提供零延迟高交互反馈
      const user = users.value.find(u => u.username === targetUsername)
      if (user) {
        user.friend_status = 'sent'
      }
    } else {
      alert(data.detail || '加好友失败')
    }
  } catch {
    alert('网络故障')
  }
}

// 跳转至通知中心同意对方的请求
const goToNotifications = () => {
  router.push('/notifications')
}

// 点击卡片直接打开该用户的个人主页弹窗
const openUserProfile = async (targetUsername) => {
  try {
    const [profileRes, postsRes] = await Promise.all([
      apiFetch(`/auth/profile/${targetUsername}`),
      apiFetch(`/moments/user/${targetUsername}`)
    ])
    if (profileRes.ok && postsRes.ok) {
      const user = await profileRes.json()
      const userPosts = await postsRes.json()
      activeProfile.value = {
        user: user,
        posts: userPosts.moments
      }
    }
  } catch {
    alert('无法加载该用户的主页')
  }
}

const isUrl = (text) => {
  if (!text) return false
  return text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')
}
</script>

<style scoped>
.search-container {
  width: 100%;
}

/* 𝕏 经典扁平化、吸顶搜索栏 */
.search-header {
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--x-border);
  padding: 12px 16px;
  z-index: 10;
}

.search-input-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #eff3f4; /* 𝕏 经典浅灰色背景 */
  border: 1px solid transparent;
  border-radius: 9999px;
  padding: 8px 16px;
  transition: all 0.15s;
}
/* 当输入框获得焦点时，药丸容器背景变纯白，边框和图标变 𝕏 蓝 */
.search-input-pill:focus-within {
  background: #ffffff;
  border-color: var(--x-blue);
  box-shadow: 0 0 0 1px var(--x-blue);
}

.search-icon-svg {
  width: 18px;
  height: 18px;
  fill: var(--x-text-gray);
  transition: fill 0.15s;
}
.search-input-pill:focus-within .search-icon-svg {
  fill: var(--x-blue);
}

.search-input-field {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.95rem;
  color: var(--x-text-main);
}

/* 搜索列表排版 */
.search-results {
  padding: 0;
}
.no-results {
  text-align: center;
  color: var(--x-text-gray);
  font-size: 0.95rem;
  padding: 60px 40px;
  line-height: 1.6;
}

/* 𝕏.com 经典“推荐关注/用户推荐”卡片排版 */
.user-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--x-border);
  cursor: pointer;
  transition: background 0.15s;
}
.user-card:hover {
  background: var(--x-bg-hover);
}

.user-card-left {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}

/* 💡 自适应头像容器，支持 Emoji 和 图片 URL 的统一性，极简融合 */
.user-avatar-small {
  width: 40px;
  height: 40px;
  background: #ffffff;
  border: 1px solid var(--x-border);
  border-radius: 50%;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  display: flex;
  flex-direction: column;
  text-align: left;
  overflow: hidden;
}
.user-nickname {
  font-weight: bold;
  font-size: 0.95rem;
  color: var(--x-text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-username {
  font-size: 0.85rem;
  color: var(--x-text-gray);
}

/* 𝕏 经典深色丸子关注按钮 */
.btn-follow-pill {
  background: #0f1419;
  color: #ffffff;
  border: none;
  font-weight: bold;
  font-size: 0.85rem;
  padding: 0 16px;
  height: 32px;
  border-radius: 9999px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}
.btn-follow-pill:hover {
  background: #272c30;
}

/* 💡 升级：精美的丸子状态色块徽章（Pill Badges） */
.badge-status {
  font-size: 0.85rem;
  font-weight: bold;
  padding: 6px 12px;
  border-radius: 9999px;
  white-space: nowrap;
}
.badge-sent {
  background: #f7f9fa;
  color: var(--x-text-gray);
  border: 1px solid var(--x-border);
}
.badge-received {
  background: #fee2e2;
  color: #ef4444;
  cursor: pointer;
  border: 1px solid #fca5a5;
  transition: background 0.2s;
}
.badge-received:hover {
  background: #fca5a5;
  color: white;
}
.badge-friends {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

/* 个人主页弹窗 (Profile) */
.modal-backdrop {
  position: fixed; top: 0; bottom: 0; left: 0; right: 0;
  background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  width: 90%; max-width: 450px; background: white; border-radius: 20px;
  max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; position: relative;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.modal-close {
  position: absolute; top: 16px; right: 16px; background: transparent; border: none; font-size: 1.25rem; font-weight: bold; cursor: pointer; color: var(--x-text-gray);
}
.modal-header { padding: 30px 24px 16px 24px; text-align: center; border-bottom: 1px solid var(--x-border); }
.modal-avatar-big {
  width: 70px; height: 70px; background: #ffffff; border: 1px solid var(--x-border); border-radius: 50%; font-size: 2.5rem; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; overflow: hidden;
}
.modal-nickname { margin: 0; font-size: 1.25rem; font-weight: 800; }
.modal-handle { margin: 4px 0 0 0; color: var(--x-text-gray); font-size: 0.9rem; }

.modal-body { flex: 1; overflow-y: auto; padding: 16px 24px; }
.modal-tab-title { font-size: 1rem; font-weight: 800; border-bottom: 2px solid var(--x-blue); padding-bottom: 6px; margin: 0 0 12px 0; display: inline-block;}
.no-posts-hint { text-align: center; color: var(--x-text-gray); font-size: 0.9rem; padding: 24px 0; }
.modal-tweet { padding: 12px 0; border-bottom: 1px solid var(--x-border); text-align: left; }
.modal-tweet-time { font-size: 0.8rem; color: var(--x-text-gray); margin-bottom: 4px; }
.modal-tweet-content { font-size: 0.95rem; line-height: 1.4; word-wrap: break-word;}
</style>