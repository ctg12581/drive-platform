<!-- src/views/SearchView.vue · 小红书风格搜索 -->
<template>
  <div class="search-container">
    <div class="search-header">
      <div class="search-input-pill">
        <svg viewBox="0 0 24 24" class="search-icon-svg"><path d="M10.5 3a7.5 7.5 0 1 1-4.55 13.46l-3.2 3.2a1 1 0 1 1-1.42-1.42l3.2-3.2A7.5 7.5 0 0 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z"/></svg>
        <input type="text" v-model="searchQuery" class="search-input-field" placeholder="搜索用户 @账号 或 个性昵称…" @input="handleSearch">
        <button v-if="searchQuery" class="search-clear" @click="clearQuery">✕</button>
      </div>
    </div>

    <div class="search-results">
      <div v-if="users.length === 0" class="xhs-empty">
        <div class="empty-emoji">🔍</div>
        <p v-if="searchQuery">没有找到与 “{{ searchQuery }}” 匹配的用户</p>
        <p v-else>输入关键字，发现更多志趣相投的朋友</p>
      </div>

      <div v-else class="result-list">
        <div v-for="user in users" :key="user.username" class="user-card" @click="openUserProfile(user.username)">
          <div class="user-card-left">
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

          <div class="user-card-right" @click.stop>
            <button v-if="user.friend_status === 'none'" @click="sendFriendRequest(user.username)" class="btn-follow-pill">
              关注
            </button>
            <span v-else-if="user.friend_status === 'sent'" class="badge-status badge-sent">已申请</span>
            <span v-else-if="user.friend_status === 'received'" class="badge-status badge-received" @click="goToNotifications">待同意</span>
            <span v-else-if="user.friend_status === 'friends'" class="badge-status badge-friends">已互关</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 个人主页弹窗 -->
    <div v-if="activeProfile" class="modal-backdrop" @click.self="activeProfile = null">
      <div class="modal-card profile-modal">
        <button class="modal-close" @click="activeProfile = null">✕</button>
        <div class="profile-cover"></div>
        <div class="profile-modal-head">
          <div class="modal-avatar-big">
            <img v-if="isUrl(activeProfile.user.avatar)" :src="activeProfile.user.avatar" class="avatar-img" />
            <span v-else-if="activeProfile.user.avatar && activeProfile.user.avatar !== '👤'">{{ activeProfile.user.avatar }}</span>
            <span v-else>{{ activeProfile.user.username[0].toUpperCase() }}</span>
          </div>
          <div class="profile-modal-meta">
            <h2 class="modal-nickname">{{ activeProfile.user.nickname }}</h2>
            <p class="modal-handle">@{{ activeProfile.user.username }}</p>
          </div>
        </div>
        <div class="modal-body">
          <h3 class="modal-tab-title">TA 的笔记 ({{ activeProfile.posts.length }})</h3>
          <div v-if="activeProfile.posts.length === 0" class="xhs-empty" style="padding:28px 0;">TA 还没有发布过任何笔记。</div>
          <div v-for="p in activeProfile.posts" :key="p.id" class="modal-note">
            <img v-if="isUrl(p.image)" :src="p.image" class="modal-note-img" loading="lazy" alt="" @error="(e) => e.target.style.display='none'" />
            <div class="modal-note-time">{{ formatLocalTime(p.time) }}</div>
            <div class="modal-note-content">{{ p.content }}</div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { isUrl } from '@drive/shared'
import { apiFetch } from '../utils/api'
import { fetchUserProfile } from '../utils/userProfile'
import { useRouter } from 'vue-router'
import { formatLocalTime } from '../utils/date'

const router = useRouter()
const searchQuery = ref('')
const users = ref([])
const activeProfile = ref(null)

let debounceTimer = null

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

const clearQuery = () => {
  searchQuery.value = ''
  users.value = []
}

const sendFriendRequest = async (targetUsername) => {
  try {
    const res = await apiFetch('/chat/add-friend', {
      method: 'POST',
      body: JSON.stringify({ friend_username: targetUsername })
    })
    const data = await res.json()
    if (res.ok) {
      alert(data.message || '请求已发送')
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

const goToNotifications = () => {
  router.push('/notifications')
}

const openUserProfile = async (targetUsername) => {
  try {
    activeProfile.value = await fetchUserProfile(targetUsername)
  } catch {
    alert('无法加载该用户的主页')
  }
}
</script>

<style scoped>
.search-container {
  width: 100%;
  background: #fff;
  min-height: calc(100vh - var(--app-top) - var(--app-bottom));
}

/* 吸顶搜索栏 */
.search-header {
  position: sticky;
  top: var(--app-top);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(14px);
  padding: 12px 16px;
  z-index: 20;
}
.search-input-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f4f4f6;
  border: 1.5px solid transparent;
  border-radius: var(--xhs-radius-pill);
  padding: 8px 16px;
  transition: all 0.16s;
}
.search-input-pill:focus-within {
  background: #fff;
  border-color: var(--xhs-red);
  box-shadow: 0 0 0 3px rgba(255, 36, 66, 0.1);
}
.search-icon-svg {
  width: 18px;
  height: 18px;
  fill: var(--xhs-text-3);
  flex-shrink: 0;
}
.search-input-pill:focus-within .search-icon-svg {
  fill: var(--xhs-red);
}
.search-input-field {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.92rem;
  color: var(--xhs-text);
}
.search-input-field::placeholder {
  color: var(--xhs-text-3);
}
.search-clear {
  border: none;
  background: #dcdce0;
  color: #fff;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  font-size: 0.6rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.empty-emoji {
  font-size: 2.6rem;
  margin-bottom: 12px;
}

.result-list {
  padding: 4px 0;
}

/* 用户卡片 */
.user-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}
.user-card:hover {
  background: #fafafa;
}
.user-card-left {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}
.user-avatar-small {
  width: 46px;
  height: 46px;
  background: #f4f4f6;
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
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--xhs-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-username {
  font-size: 0.82rem;
  color: var(--xhs-text-3);
  margin-top: 2px;
}

.btn-follow-pill {
  background: var(--xhs-red);
  color: #fff;
  border: none;
  font-weight: 700;
  font-size: 0.82rem;
  padding: 0 20px;
  height: 32px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
  transition: background 0.18s;
  white-space: nowrap;
  box-shadow: 0 3px 10px rgba(255, 36, 66, 0.22);
}
.btn-follow-pill:hover {
  background: #ef1b38;
}

.badge-status {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: var(--xhs-radius-pill);
  white-space: nowrap;
}
.badge-sent {
  background: #f4f4f6;
  color: var(--xhs-text-3);
}
.badge-received {
  background: var(--xhs-red-soft);
  color: var(--xhs-red);
  cursor: pointer;
  border: 1px solid var(--xhs-red-line);
}
.badge-friends {
  background: #eef9f1;
  color: #1f9d55;
}

/* 弹窗 */
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
  max-width: 420px;
  background: #fff;
  border-radius: 22px;
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
}
.profile-cover {
  height: 92px;
  background: linear-gradient(135deg, #ffd9e1, #ffeef2 60%, #fff);
}
.modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 3;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.28);
  color: #fff;
  border: none;
  font-size: 0.8rem;
  cursor: pointer;
}
.profile-modal-head {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding: 0 22px 16px;
  margin-top: -30px;
}
.modal-avatar-big {
  width: 68px;
  height: 68px;
  background: #fff;
  border-radius: 50%;
  font-size: 2.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 0 0 3px #fff, 0 4px 14px rgba(0, 0, 0, 0.12);
}
.profile-modal-meta {
  padding-bottom: 4px;
}
.modal-nickname {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
}
.modal-handle {
  margin: 3px 0 0;
  color: var(--xhs-text-3);
  font-size: 0.82rem;
}
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 4px 22px 22px;
}
.modal-tab-title {
  font-size: 0.92rem;
  font-weight: 800;
  margin: 6px 0 12px;
}
.modal-note {
  padding: 12px 0;
  border-bottom: 1px solid var(--xhs-line);
  text-align: left;
}
.modal-note-img {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 8px;
  display: block;
}
.modal-note-time {
  font-size: 0.72rem;
  color: var(--xhs-text-3);
  margin-bottom: 5px;
}
.modal-note-content {
  font-size: 0.92rem;
  line-height: 1.55;
  word-wrap: break-word;
}
</style>
