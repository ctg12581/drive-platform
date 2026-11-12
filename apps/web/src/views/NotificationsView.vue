<!-- src/views/NotificationsView.vue · 小红书风格通知 -->
<template>
  <div class="notify-container">
    <div class="notify-header">
      <h2 class="notify-title">新的关注</h2>
      <span class="notify-sub">好友申请</span>
    </div>

    <div class="notify-list">
      <div v-if="requests.length === 0" class="xhs-empty">
        <div class="empty-emoji">🔔</div>
        <h3 class="empty-h3">暂时没有新消息</h3>
        <p class="empty-p">当有人向你发起关注 / 好友申请时，会出现在这里。</p>
      </div>

      <div v-else v-for="req in requests" :key="req.id" class="notify-card">
        <div class="notify-card-left">
          <div class="notify-avatar">
            <img v-if="isUrl(req.avatar)" :src="req.avatar" class="avatar-img" />
            <span v-else>{{ req.avatar }}</span>
          </div>
          <div class="notify-content">
            <div class="user-meta">
              <span class="user-nickname">{{ req.nickname }}</span>
              <span class="user-handle">@{{ req.username }}</span>
            </div>
            <p class="notify-desc">请求添加你为好友，同意后即可开始聊天。</p>
          </div>
        </div>

        <div class="notify-card-right">
          <button @click="handleAction(req.id, 'reject')" class="btn-action reject-btn">忽略</button>
          <button @click="handleAction(req.id, 'accept')" class="btn-action accept-btn">同意</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { isUrl } from '@drive/shared'
import { useChatStore } from '../store/chat'
import { apiFetch } from '../utils/api'

const chatStore = useChatStore()
const requests = ref([])

onMounted(() => {
  fetchPendingRequests()
  window.addEventListener('chat:friend-requests-changed', fetchPendingRequests)
})

onUnmounted(() => {
  window.removeEventListener('chat:friend-requests-changed', fetchPendingRequests)
})

const fetchPendingRequests = async () => {
  try {
    const res = await apiFetch('/chat/friend-requests/pending')
    const data = await res.json()
    if (res.ok) {
      requests.value = data.requests
      chatStore.pendingRequestsCount = data.requests.length
    }
  } catch {
    console.error('获取通知列表失败')
  }
}

const handleAction = async (requestId, action) => {
  const endpoint = `/chat/friend-requests/${action}`
  try {
    const res = await apiFetch(endpoint, {
      method: 'POST',
      body: JSON.stringify({ request_id: requestId })
    })
    if (res.ok) {
      requests.value = requests.value.filter(r => r.id !== requestId)
      chatStore.pendingRequestsCount = requests.value.length
    }
  } catch {
    alert('请求处理失败')
  }
}
</script>

<style scoped>
.notify-container {
  width: 100%;
  background: #fff;
  min-height: calc(100vh - var(--app-top) - var(--app-bottom));
}

.notify-header {
  position: sticky;
  top: var(--app-top);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--xhs-line);
  padding: 16px;
  z-index: 20;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.notify-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--xhs-text);
}
.notify-sub {
  font-size: 0.78rem;
  color: var(--xhs-text-3);
}

.empty-emoji {
  font-size: 3rem;
  margin-bottom: 10px;
}
.empty-h3 {
  font-size: 1.15rem;
  font-weight: 800;
  margin: 8px 0 6px;
  color: var(--xhs-text);
}
.empty-p {
  max-width: 260px;
  margin: 0 auto;
}

/* 通知卡片 */
.notify-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-bottom: 1px solid var(--xhs-line);
  gap: 14px;
  animation: xhs-fade-up 0.25s ease both;
}
.notify-card-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
}
.notify-avatar {
  width: 48px;
  height: 48px;
  background: #f4f4f6;
  border-radius: 50%;
  font-size: 1.6rem;
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
.notify-content {
  display: flex;
  flex-direction: column;
}
.user-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.user-nickname {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--xhs-text);
}
.user-handle {
  font-size: 0.8rem;
  color: var(--xhs-text-3);
}
.notify-desc {
  margin: 5px 0 0 0;
  font-size: 0.88rem;
  color: var(--xhs-text-2);
  line-height: 1.45;
}

.notify-card-right {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.btn-action {
  border: none;
  font-weight: 700;
  font-size: 0.84rem;
  padding: 0 22px;
  height: 34px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
  transition: background 0.16s;
  white-space: nowrap;
}
.accept-btn {
  background: var(--xhs-red);
  color: #fff;
  box-shadow: 0 3px 10px rgba(255, 36, 66, 0.22);
}
.accept-btn:hover {
  background: #ef1b38;
}
.reject-btn {
  background: #f4f4f6;
  color: var(--xhs-text-2);
}
.reject-btn:hover {
  background: #eaeaee;
}
</style>
