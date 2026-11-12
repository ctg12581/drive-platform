<!-- src/views/ChatView.vue · 小红书风格私信 -->
<template>
  <div class="x-dm-layout">

    <!-- 左侧：联系人列表 -->
    <div :class="['contacts-sidebar', { 'hide-on-mobile': selectedContact }]">
      <div class="sidebar-header">
        <h3 class="sidebar-title">消息</h3>
        <button @click="showAddModal = !showAddModal" class="btn-icon" aria-label="添加好友">
          <svg viewBox="0 0 24 24" class="svg-inline"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        </button>
      </div>

      <!-- 加好友面板 -->
      <div v-if="showAddModal" class="add-friend-panel">
        <input type="text" v-model="newFriendUsername" placeholder="添加好友的用户名…" @keyup.enter="addFriend">
        <button @click="addFriend" class="x-btn-pill">添加</button>
      </div>

      <!-- 好友列表 -->
      <div class="contacts-list">
        <div v-if="friends.length === 0" class="no-contacts">
          暂无联系人<br/>点击右上角 “＋” 添加好友开始聊天
        </div>
        <div v-for="friend in friends" :key="friend.username"
             :class="['contact-item', { active: selectedContact === friend.username }]"
             @click="selectContact(friend.username)">

          <div class="contact-avatar" @click.stop="openUserProfile(friend.username)">
            <img v-if="isUrl(friend.avatar)" :src="friend.avatar" class="avatar-img" />
            <span v-else-if="friend.avatar && friend.avatar !== '👤'">{{ friend.avatar }}</span>
            <span v-else>{{ friend.username[0].toUpperCase() }}</span>
          </div>

          <div class="contact-details-row">
            <div class="contact-details">
              <div class="contact-name-row">
                <span class="contact-name">{{ friend.nickname }}</span>
                <span class="contact-time-sub">{{ formatLocalTime(friend.last_message_time, 'HH:mm') }}</span>
              </div>
              <div class="contact-last-msg">{{ friend.last_message || '点击开始对话' }}</div>
            </div>
            <div v-if="friend.unread > 0" class="unread-badge">{{ friend.unread }}</div>
          </div>

        </div>
      </div>
    </div>

    <!-- 右侧：活动对话区 -->
    <div :class="['chat-main', { 'hide-on-mobile': !selectedContact }]">

      <div v-if="!selectedContact" class="welcome-box">
        <div class="welcome-emoji">💬</div>
        <h2 class="welcome-title">选择一个联系人</h2>
        <p class="welcome-sub">从联系人列表中选择，或点击右上角添加新朋友开启对话</p>
      </div>

      <div v-else class="chat-window">
        <div class="chat-header">
          <div class="chat-header-left">
            <button @click="selectedContact = null" class="btn-back">
              <svg viewBox="0 0 24 24" class="svg-inline"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
            </button>
            <div class="header-info" @click="openUserProfile(selectedContact)" style="cursor: pointer;">
              <span class="header-name">{{ selectedContactProfile?.nickname || selectedContact }}</span>
              <span class="header-status">{{ chatStore.connected ? '在线' : '离线' }} · @{{ selectedContact }}</span>
            </div>
          </div>
        </div>

        <div class="chat-body" id="chatFlow" @scroll.passive="handleChatScroll">
          <div v-for="(msg, idx) in messages" :key="msg.id || msg.client_id || idx"
               :class="['message-row', msg.system ? 'sys-row' : (msg.self ? 'self-row' : 'peer-row')]">

            <div v-if="!msg.system" class="msg-bubble" @click.stop="toggleMessageMenu(idx)">
              <img v-if="isImageUrl(msg.text)" :src="msg.text" class="chat-img" @load="scrollToBottom" />
              <span v-else>{{ msg.text }}</span>
              <div class="msg-meta">
                <span v-if="msg.self" :class="['read-status', { 'status-read': msg.is_read }]">
                  {{ msg.is_read ? '已读' : '未读' }}
                </span>
                <span class="msg-time">{{ msg.time }}</span>
              </div>

              <div v-if="activeMenuIndex === idx" class="telegram-menu" @click.stop>
                <button class="menu-item" @click="handleCopy(msg.text)">
                  <svg viewBox="0 0 24 24" class="menu-icon"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
                  复制文本
                </button>
                <div v-if="msg.self && msg.id" class="menu-divider"></div>
                <button v-if="msg.self && msg.id" class="menu-item delete-btn" @click="handleRecall(msg.id, idx)">
                  <svg viewBox="0 0 24 24" class="menu-icon"><path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                  撤回消息
                </button>
              </div>
            </div>

            <div v-else class="sys-notice">{{ msg.text }}</div>
          </div>
        </div>

        <div class="chat-footer">
          <div class="input-pill">
            <input type="file" ref="fileInput" style="display: none" accept="image/*" @change="handleImageUpload">

            <button @click="triggerImageSelect" class="btn-icon" :disabled="!chatStore.connected" style="padding-top: 3px;">
              <svg viewBox="0 0 24 24" class="svg-inline" style="color: var(--xhs-text-3);"><path d="M19.75 2H4.25C3.01 2 2 3.01 2 4.25v15.5C2 20.99 3.01 22 4.25 22h15.5c1.24 0 2.25-1.01 2.25-2.25V4.25C22 3.01 20.99 2 19.75 2zM4.25 3.5h15.5c.41 0 .75.34.75.75v10.12l-3.21-3.21c-.29-.29-.77-.29-1.06 0l-3.87 3.87-2.31-2.31a.75.75 0 00-1.06 0L3.5 16.5V4.25c0-.41.34-.75.75-.75zM3.5 18.62l5.03-5.03 2.84 2.84c.29.29.77.29 1.06 0l-3.34-3.34 3.77 3.77V19.75c0 .41-.34.75-.75.75H4.25c-.41 0-.75-.34-.75-.75v-1.13zM8.5 11c1.38 0 2.5-1.12 2.5-2.5S9.88 6 8.5 6 6 7.12 6 8.5 7.12 11 8.5 11zm0-3.5c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"/></svg>
            </button>

            <input type="text" v-model="messageInput" placeholder="发消息…" @keyup.enter="sendMessage" :disabled="!chatStore.connected">
            <button @click="sendMessage" class="btn-send" :disabled="!messageInput.trim() || !chatStore.connected">
              <svg viewBox="0 0 24 24" class="svg-inline"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
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
            <img v-if="isUrl(activeProfile.user.avatar)" :src="activeProfile.user.avatar" class="avatar-img-el" />
            <span v-else-if="activeProfile.user.avatar && activeProfile.user.avatar !== '👤'">{{ activeProfile.user.avatar }}</span>
            <span v-else>{{ activeProfile.user.username[0].toUpperCase() }}</span>
          </div>
          <div class="profile-modal-meta">
            <h2 class="modal-nickname">{{ activeProfile.user.nickname }}</h2>
            <p class="modal-handle">@{{ activeProfile.user.username }}</p>
          </div>
        </div>
        <div v-if="isCurrentFriend && activeProfile.user.username !== authStore.username" class="profile-delete-wrap">
          <button @click="handleDeleteFriend(activeProfile.user.username)" class="btn-profile-delete">解除好友关系</button>
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
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { isUrl, isImageUrl } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import { useChatStore } from '../store/chat'
import { formatLocalTime } from '../utils/date'
import { apiFetch, API_BASE } from '../utils/api'
import { fetchUserProfile } from '../utils/userProfile'

const authStore = useAuthStore()
const chatStore = useChatStore()
const showAddModal = ref(false)
const newFriendUsername = ref('')

const friends = computed(() => chatStore.cachedFriends)
const selectedContact = ref(chatStore.activeContact)
const messageInput = ref('')

const messages = computed(() => chatStore.activeMessages)

const fileInput = ref(null)
const activeProfile = ref(null)
const activeMenuIndex = ref(null)
const chatFlowNearBottom = ref(true)

const selectedContactProfile = computed(() => {
  return friends.value.find(f => f.username === selectedContact.value)
})

const isCurrentFriend = computed(() => {
  if (!activeProfile.value) return false
  return friends.value.some(f => f.username === activeProfile.value.user.username)
})

watch(selectedContact, (newVal) => {
  chatStore.setActiveContact(newVal)
})

onMounted(() => {
  fetchFriends()
  if (selectedContact.value) {
    selectContact(selectedContact.value)
  }
  window.addEventListener('click', closeAllMenus)
})

onUnmounted(() => {
  selectedContact.value = null
  chatStore.setActiveContact(null)
  window.removeEventListener('click', closeAllMenus)
})

const closeAllMenus = () => {
  activeMenuIndex.value = null
}

const toggleMessageMenu = (index) => {
  if (activeMenuIndex.value === index) {
    activeMenuIndex.value = null
  } else {
    activeMenuIndex.value = index
  }
}

const handleCopy = (text) => {
  try {
    navigator.clipboard.writeText(text)
    alert('已复制到剪贴板')
  } catch (err) {
    console.error('复制失败', err)
  }
  activeMenuIndex.value = null
}

const handleRecall = (messageId, index) => {
  activeMenuIndex.value = null
  if (!chatStore.connected || !selectedContact.value) return

  if (!window.confirm('确定要撤回这条消息吗？')) {
    return
  }

  chatStore.sendWebSocketPayload({
    type: 'recall',
    to: selectedContact.value,
    message_id: messageId
  })

  chatStore.activeMessages.splice(index, 1, {
    system: true,
    text: '你撤回了一条消息'
  })

  chatStore.updateLastMessageState(selectedContact.value, '你撤回了一条消息', true, '', true)
  chatStore.setHistory(selectedContact.value, [...chatStore.activeMessages])
}

const handleDeleteFriend = async (friendUsername) => {
  if (!window.confirm(`确定要解除与 @${friendUsername} 的好友关系吗？（你们的历史聊天记录仍将安全保留）`)) {
    return
  }
  try {
    const res = await apiFetch('/chat/friend/delete', {
      method: 'POST',
      body: JSON.stringify({ friend_username: friendUsername })
    })

    if (res.ok) {
      activeProfile.value = null
      selectedContact.value = null
      fetchFriends()
    } else {
      alert('解除好友失败')
    }
  } catch (err) {
    console.error(err)
    alert('请求失败')
  }
}

const fetchFriends = () => chatStore.fetchFriends()

const addFriend = async () => {
  const friend = newFriendUsername.value.trim()
  if (!friend) return
  try {
    const res = await apiFetch('/chat/add-friend', {
      method: 'POST',
      body: JSON.stringify({ friend_username: friend })
    })
    const data = await res.json()
    if (res.ok) {
      alert(data.message)
      newFriendUsername.value = ''
      showAddModal.value = false
      fetchFriends()
    } else {
      alert(data.detail || '加好友失败')
    }
  } catch {
    alert('网络故障')
  }
}

const selectContact = async (friendUsername) => {
  selectedContact.value = friendUsername

  const cachedHistory = chatStore.cachedHistory[friendUsername] || []
  chatStore.activeMessages = [...cachedHistory]
  scrollToBottom()

  const friend = friends.value.find(f => f.username === friendUsername)
  if (friend) {
    friend.unread = 0
    chatStore.setFriends([...chatStore.cachedFriends])
  }

  chatStore.sendWebSocketPayload({ type: 'read', to: friendUsername })

  try {
    const res = await apiFetch(`/chat/history/${friendUsername}`)
    const data = await res.json()
    if (res.ok) {
      const localizedHistory = data.history.map(msg => ({
        ...msg,
        time: formatLocalTime(msg.time)
      }))
      chatStore.setHistory(friendUsername, localizedHistory)
      chatStore.activeMessages = [...localizedHistory]
      scrollToBottom()
    }
  } catch (err) {
    console.error('获取历史记录失败:', err)
  }
}

const sendMessage = () => {
  if (!chatStore.connected || !selectedContact.value) return
  const text = messageInput.value.trim()
  if (!text) return

  const clientId = (crypto?.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random()}`
  chatStore.sendWebSocketPayload({
    type: 'msg',
    to: selectedContact.value,
    message: text,
    client_id: clientId
  })

  chatStore.activeMessages.push({
    id: null,
    client_id: clientId,
    from: authStore.username,
    text: text,
    time: getCurrentTimeLabel(),
    self: true,
    system: false,
    is_read: false
  })

  chatStore.updateLastMessageState(selectedContact.value, text, true)
  chatStore.setHistory(selectedContact.value, [...chatStore.activeMessages])

  messageInput.value = ''
  scrollToBottom()
}

const openUserProfile = async (targetUsername) => {
  try {
    activeProfile.value = await fetchUserProfile(targetUsername)
  } catch (err) {
    console.error('加载主页异常:', err)
    alert('无法加载该用户的主页')
  }
}

const triggerImageSelect = () => {
  if (fileInput.value) { fileInput.value.click() }
}

const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    alert('图片过大，限制上传小于 2MB 的图片。')
    event.target.value = ''
    return
  }

  const localPreviewUrl = URL.createObjectURL(file)

  if (!window.confirm('确定要向对方发送选择的这张图片吗？')) {
    URL.revokeObjectURL(localPreviewUrl)
    event.target.value = ''
    return
  }

  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await apiFetch('/chat/upload', {
      method: 'POST',
      body: formData
    })
    const data = await res.json()

    if (res.ok && data.success) {
      const imageUrl = data.url.startsWith('http') ? data.url : `${API_BASE}${data.url}`

      const clientId = (crypto?.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random()}`
      chatStore.sendWebSocketPayload({
        type: 'msg',
        to: selectedContact.value,
        message: imageUrl,
        client_id: clientId
      })

      chatStore.activeMessages.push({
        id: null,
        client_id: clientId,
        from: authStore.username,
        text: imageUrl,
        time: getCurrentTimeLabel(),
        self: true,
        system: false,
        is_read: false
      })

      chatStore.updateLastMessageState(selectedContact.value, '[图片]', true)
      chatStore.setHistory(selectedContact.value, [...chatStore.activeMessages])
    } else {
      alert(data.detail || '图片上传失败')
    }
  } catch (err) {
    console.error(err)
    alert('上传图片过程中发生网络故障')
  } finally {
    URL.revokeObjectURL(localPreviewUrl)
    event.target.value = ''
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    const flow = document.getElementById('chatFlow')
    if (flow) {
      flow.scrollTop = flow.scrollHeight
      chatFlowNearBottom.value = true
    }
  })
}

const handleChatScroll = () => {
  const flow = document.getElementById('chatFlow')
  if (!flow) return
  chatFlowNearBottom.value = flow.scrollHeight - flow.clientHeight - flow.scrollTop <= 120
}

watch(
  () => messages.value.length,
  (newLen, oldLen) => {
    if (newLen > oldLen && chatFlowNearBottom.value) {
      scrollToBottom()
    }
  },
)

const resyncActiveHistory = async () => {
  const friend = selectedContact.value
  if (!friend) return
  try {
    const res = await apiFetch(`/chat/history/${friend}`)
    const data = await res.json()
    if (!res.ok || selectedContact.value !== friend) return
    const localizedHistory = data.history.map((msg) => ({
      ...msg,
      time: formatLocalTime(msg.time),
    }))
    chatStore.setHistory(friend, localizedHistory)
    chatStore.activeMessages = [...localizedHistory]
    if (chatFlowNearBottom.value) scrollToBottom()
  } catch (err) {
    console.error('重连后同步聊天历史失败:', err)
  }
}

watch(
  () => chatStore.resyncTick,
  () => {
    resyncActiveHistory()
  },
)

const getCurrentTimeLabel = () => {
  const now = new Date()
  return `${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
/* 小红书风格私信布局 */
.x-dm-layout {
  display: flex;
  height: calc(100vh - var(--app-top) - var(--app-bottom));
  width: 100%;
  background: #fff;
}

/* 左侧联系人 */
.contacts-sidebar {
  width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--xhs-line);
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(14px);
  z-index: 5;
}
.sidebar-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
}
.btn-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--xhs-red);
  display: flex;
  align-items: center;
}
.svg-inline { width: 22px; height: 22px; fill: currentColor; }

.add-friend-panel {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--xhs-line);
  background: #fafafa;
}
.add-friend-panel input {
  flex: 1;
  padding: 7px 14px;
  border: 1px solid var(--xhs-line);
  border-radius: var(--xhs-radius-pill);
  outline: none;
  font-size: 0.88rem;
  background: #fff;
  color: var(--xhs-text);
}
.add-friend-panel input:focus { border-color: var(--xhs-red); }
.x-btn-pill {
  background: var(--xhs-red);
  color: #fff;
  border: none;
  padding: 0 18px;
  border-radius: var(--xhs-radius-pill);
  font-weight: 700;
  font-size: 0.84rem;
  cursor: pointer;
}

.contacts-list { flex: 1; overflow-y: auto; }
.no-contacts {
  padding: 60px 30px;
  text-align: center;
  color: var(--xhs-text-3);
  font-size: 0.9rem;
  line-height: 1.7;
}
.contact-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.18s;
}
.contact-item:active { background: #fafafa; }
.contact-item.active { background: var(--xhs-red-soft); }

.contact-details-row {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}
.contact-details { display: flex; flex-direction: column; text-align: left; overflow: hidden; flex: 1; }
.contact-name-row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.contact-name { font-weight: 700; font-size: 0.95rem; color: var(--xhs-text); }
.contact-time-sub { font-size: 0.72rem; color: var(--xhs-text-3); margin-left: 8px; }
.contact-last-msg {
  font-size: 0.8rem;
  color: var(--xhs-text-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 3px;
  text-align: left;
}

.unread-badge {
  background: var(--xhs-red);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: var(--xhs-radius-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  box-sizing: border-box;
  animation: xhs-pop 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes xhs-pop {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}

.contact-avatar {
  width: 46px;
  height: 46px;
  background: #f4f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
  color: var(--xhs-text-2);
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }

/* 右侧聊天 */
.chat-main { width: 100%; display: flex; flex-direction: column; }
.welcome-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 24px;
}
.welcome-emoji { font-size: 3rem; margin-bottom: 12px; }
.welcome-title { font-size: 1.15rem; font-weight: 800; margin: 0 0 8px; }
.welcome-sub { color: var(--xhs-text-3); font-size: 0.88rem; max-width: 260px; }

.chat-window { display: flex; flex-direction: column; height: 100%; }
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--xhs-line);
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(14px);
  z-index: 5;
}
.chat-header-left { display: flex; align-items: center; gap: 10px; }
.btn-back { background: transparent; border: none; cursor: pointer; color: var(--xhs-text); display: flex; align-items: center; }
.header-info { display: flex; flex-direction: column; }
.header-name { font-weight: 700; font-size: 0.95rem; }
.header-status { font-size: 0.76rem; color: var(--xhs-text-3); }

.chat-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f7f7f8;
}
.message-row { display: flex; width: 100%; }
.self-row { justify-content: flex-end; }
.peer-row { justify-content: flex-start; }
.sys-row { justify-content: center; }

.msg-bubble {
  max-width: 72%;
  padding: 9px 13px;
  font-size: 0.92rem;
  line-height: 1.45;
  word-wrap: break-word;
  position: relative;
  cursor: pointer;
  user-select: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.self-row .msg-bubble {
  background: var(--xhs-red);
  color: #fff;
  border-radius: 18px 18px 4px 18px;
}
.peer-row .msg-bubble {
  background: #fff;
  color: var(--xhs-text);
  border-radius: 18px 18px 18px 4px;
}

.msg-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 4px;
  font-size: 0.66rem;
}
.read-status { opacity: 0.75; color: #ffe0e5; font-weight: 700; }
.read-status.status-read { color: #fff; opacity: 0.9; }
.msg-time { display: block; opacity: 0.75; text-align: right; }
.peer-row .read-status { display: none !important; }
.peer-row .msg-meta { justify-content: flex-end; }
.peer-row .msg-time { color: var(--xhs-text-3); }

.telegram-menu {
  position: absolute;
  bottom: calc(100% + 4px);
  background: rgba(28, 28, 30, 0.96);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
  padding: 6px;
  z-index: 210;
  display: flex;
  flex-direction: column;
  min-width: 120px;
  animation: xhs-fade-up 0.15s ease;
}
.self-row .telegram-menu { right: 8px; transform-origin: bottom right; }
.peer-row .telegram-menu { left: 8px; transform-origin: bottom left; }
.menu-item {
  background: transparent;
  border: none;
  padding: 10px 14px;
  text-align: left;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.15s;
}
.menu-item:hover { background: rgba(255, 255, 255, 0.1); }
.menu-icon { width: 16px; height: 16px; fill: currentColor; }
.menu-divider { height: 1px; background: rgba(255, 255, 255, 0.08); margin: 4px 6px; }
.menu-item.delete-btn { color: #ff6b81; }
.menu-item.delete-btn:hover { background: rgba(255, 77, 79, 0.15); }

.sys-notice {
  font-size: 0.76rem;
  color: var(--xhs-text-3);
  background: rgba(0, 0, 0, 0.04);
  padding: 4px 14px;
  border-radius: var(--xhs-radius-pill);
}

.chat-img {
  max-width: 100%;
  max-height: 220px;
  border-radius: 12px;
  display: block;
  margin-top: 4px;
  cursor: pointer;
}

.chat-footer {
  padding: 10px 14px;
  border-top: 1px solid var(--xhs-line);
  background: #fff;
}
.input-pill {
  display: flex;
  align-items: center;
  background: #f4f4f6;
  border-radius: var(--xhs-radius-pill);
  padding: 5px 14px;
  gap: 8px;
}
.input-pill input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.92rem;
  height: 34px;
  color: var(--xhs-text);
}
.btn-send { background: transparent; border: none; cursor: pointer; display: flex; align-items: center; color: var(--xhs-red); }
.btn-send:disabled { color: var(--xhs-text-3); cursor: not-allowed; }

/* 个人主页弹窗 */
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
.profile-cover { height: 92px; background: linear-gradient(135deg, #ffd9e1, #ffeef2 60%, #fff); }
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
  padding: 0 22px 14px;
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
.profile-modal-meta { padding-bottom: 4px; }
.modal-nickname { margin: 0; font-size: 1.2rem; font-weight: 800; }
.modal-handle { margin: 3px 0 0; color: var(--xhs-text-3); font-size: 0.82rem; }

.profile-delete-wrap { padding: 0 22px 14px; }
.btn-profile-delete {
  background: transparent;
  color: var(--xhs-red);
  border: 1px solid var(--xhs-red-line);
  font-weight: 700;
  font-size: 0.82rem;
  padding: 0 18px;
  height: 32px;
  border-radius: var(--xhs-radius-pill);
  cursor: pointer;
  transition: background 0.2s;
}
.btn-profile-delete:hover { background: var(--xhs-red-soft); }

.modal-body { flex: 1; overflow-y: auto; padding: 4px 22px 22px; }
.modal-tab-title { font-size: 0.92rem; font-weight: 800; margin: 6px 0 12px; }
.no-posts-hint { text-align: center; color: var(--xhs-text-3); font-size: 0.88rem; padding: 24px 0; }
.modal-note { padding: 12px 0; border-bottom: 1px solid var(--xhs-line); text-align: left; }
.modal-note-img { width: 100%; max-height: 200px; object-fit: cover; border-radius: 12px; margin-bottom: 8px; display: block; }
.modal-note-time { font-size: 0.72rem; color: var(--xhs-text-3); margin-bottom: 5px; }
.modal-note-content { font-size: 0.92rem; line-height: 1.55; word-wrap: break-word; }

/* 移动端单栏 */
.contacts-sidebar.hide-on-mobile { display: none !important; }
.chat-main.hide-on-mobile { display: none !important; }
.btn-back { display: block !important; }
</style>
