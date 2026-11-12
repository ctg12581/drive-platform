<!-- src/views/NotificationsView.vue -->
<template>
  <div class="notify-container">
    <!-- 𝕏 经典吸顶头部栏 -->
    <div class="notify-header">
      <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800;">系统通知</h2>
    </div>

    <!-- 待审批列表 -->
    <div class="notify-list">
      <div v-if="requests.length === 0" class="no-notify">
        <div style="font-size: 3rem; margin-bottom: 12px;">🔔</div>
        <h3>保持干净！</h3>
        <p style="color: var(--x-text-gray); max-width: 280px; margin: 0 auto; line-height: 1.5;">
          当有其他用户向您发起关注或加好友申请时，您将在这里收到实时通知。
        </p>
      </div>

      <div v-else v-for="req in requests" :key="req.id" class="notify-card">
        <div class="notify-card-left">
          <!-- 头像自适应渲染 -->
          <div class="notify-avatar">
            <img v-if="isUrl(req.avatar)" :src="req.avatar" class="avatar-img" />
            <span v-else>{{ req.avatar }}</span>
          </div>
          <div class="notify-content">
            <div class="user-meta">
              <span class="user-nickname">{{ req.nickname }}</span>
              <span class="user-handle">@{{ req.username }}</span>
            </div>
            <p class="notify-desc">向您发送了双向好友申请，同意后即可开始互粉聊天。</p>
          </div>
        </div>
        
        <!-- 操作按钮组 -->
        <div class="notify-card-right">
          <button @click="handleAction(req.id, 'accept')" class="btn-action accept-btn">同意</button>
          <button @click="handleAction(req.id, 'reject')" class="btn-action reject-btn">拒绝</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '../store/chat'
import { apiFetch } from '../utils/api'
import { formatLocalTime } from '../utils/date'

const chatStore = useChatStore()
const requests = ref([])

onMounted(() => {
  fetchPendingRequests()
})

const fetchPendingRequests = async () => {
  try {
    const res = await apiFetch('/chat/friend-requests/pending')
    const data = await res.json()
    if (res.ok) {
      requests.value = data.requests
      // 实时同步更新全局未读数
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
      // 动画式从本地过滤删除，并更新计数器
      requests.value = requests.value.filter(r => r.id !== requestId)
      chatStore.pendingRequestsCount = requests.value.length
    }
  } catch {
    alert('请求处理失败')
  }
}

const isUrl = (text) => {
  if (!text) return false
  return text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')
}
</script>

<style scoped>
.notify-container {
  width: 100%;
}

/* 吸顶毛玻璃通知栏 */
.notify-header {
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--x-border);
  padding: 16px;
  z-index: 10;
  text-align: left;
}

.no-notify {
  text-align: center;
  padding: 80px 20px;
  color: var(--x-text-main);
}
.no-notify h3 {
  font-size: 1.5rem;
  font-weight: 800;
  margin: 12px 0 8px 0;
}

/* 通知卡片排版 */
.notify-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-bottom: 1px solid var(--x-border);
  gap: 16px;
}
@media (min-width: 500px) {
  .notify-card {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.notify-card-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
}

/* 头像容器 */
.notify-avatar {
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

.notify-content {
  display: flex;
  flex-direction: column;
}
.user-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}
.user-nickname {
  font-weight: bold;
  font-size: 0.95rem;
  color: var(--x-text-main);
}
.user-handle {
  font-size: 0.85rem;
  color: var(--x-text-gray);
}
.notify-desc {
  margin: 6px 0 0 0;
  font-size: 0.95rem;
  color: var(--x-text-main);
  line-height: 1.4;
}

/* 右侧操作栏 */
.notify-card-right {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-action {
  border: none;
  font-weight: bold;
  font-size: 0.85rem;
  padding: 0 16px;
  height: 32px;
  border-radius: 9999px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.accept-btn {
  background: var(--x-blue);
  color: white;
}
.accept-btn:hover {
  background: #1a8cd8;
}
.reject-btn {
  background: transparent;
  border: 1px solid #fca5a5;
  color: #ef4444;
}
.reject-btn:hover {
  background: #fee2e2;
  border-color: #ef4444;
}
</style>