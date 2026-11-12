<!-- src/views/ChatView.vue (除了 <style> 外的完整最新代码) -->
<template>
  <div class="x-dm-layout">
    
    <!-- 左侧：联系人列表 -->
    <div :class="['contacts-sidebar', { 'hide-on-mobile': selectedContact }]">
      <div class="sidebar-header">
        <h3 style="margin: 0;">私信信箱</h3>
        <button @click="showAddModal = !showAddModal" class="btn-icon">
          <svg viewBox="0 0 24 24" class="svg-inline"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
        </button>
      </div>

      <!-- 加好友面板 -->
      <div v-if="showAddModal" class="add-friend-panel">
        <input type="text" v-model="newFriendUsername" placeholder="添加好友的用户名..." @keyup.enter="addFriend">
        <button @click="addFriend" class="x-btn-pill">加好友</button>
      </div>

      <!-- 好友列表 -->
      <div class="contacts-list">
        <div v-if="friends.length === 0" class="no-contacts">
          暂无联系人，点击上方 “+” 添加好友开始聊天。
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
                <span class="contact-time-sub">{{ friend.last_message_time }}</span>
              </div>
              <div class="contact-last-msg">{{ friend.last_message || '点击开始对话' }}</div>
            </div>
            <div v-if="friend.unread > 0" class="unread-badge">
              {{ friend.unread }}
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- 右侧：活动对话区 -->
    <div :class="['chat-main', { 'hide-on-mobile': !selectedContact }]">
      
      <!-- 未选择联系人提示 -->
      <div v-if="!selectedContact" class="welcome-box">
        <div style="font-size: 3rem; margin-bottom: 12px;">✉️</div>
        <h2>选择一个联系人</h2>
        <p style="color: var(--x-text-gray);">从现有的联系人列表中选择，或点击左侧添加新朋友以开启对话。</p>
      </div>

      <!-- 活动聊天窗口 -->
      <div v-else class="chat-window">
        <!-- 窗口头部 -->
        <div class="chat-header">
          <div class="chat-header-left">
            <button @click="selectedContact = null" class="btn-back">
              <svg viewBox="0 0 24 24" class="svg-inline"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
            </button>
            <div class="header-info" @click="openUserProfile(selectedContact)" style="cursor: pointer;">
              <span class="header-name">{{ selectedContactProfile?.nickname || selectedContact }}</span>
              <span class="header-status">@{{ selectedContact }} · {{ chatStore.connected ? '在线' : '离线' }}</span>
            </div>
          </div>
        </div>

        <!-- 对话消息池 -->
        <div class="chat-body" id="chatFlow">
          <div v-for="(msg, idx) in messages" :key="idx" 
               :class="['message-row', msg.system ? 'sys-row' : (msg.self ? 'self-row' : 'peer-row')]">
            
            <!-- 气泡主体 -->
            <div v-if="!msg.system" class="msg-bubble" @click.stop="toggleMessageMenu(idx)">
              <img v-if="isImage(msg.text)" :src="msg.text" class="chat-img" @load="scrollToBottom" />
              <span v-else>{{ msg.text }}</span>
              <div class="msg-meta">
                <span v-if="msg.self" :class="['read-status', { 'status-read': msg.is_read }]">
                  {{ msg.is_read ? '已读' : '未读' }}
                </span>
                <span class="msg-time">{{ msg.time }}</span>
              </div>

              <!-- Telegram 操作菜单 -->
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
            
            <!-- 撤回提示 -->
            <div v-else class="sys-notice">{{ msg.text }}</div>
          </div>
        </div>

        <!-- 底部消息发送栏 -->
        <div class="chat-footer">
          <div class="input-pill">
            <input type="file" ref="fileInput" style="display: none" accept="image/*" @change="handleImageUpload">
            
            <button @click="triggerImageSelect" class="btn-icon" :disabled="!chatStore.connected" style="padding-top: 3px;">
              <svg viewBox="0 0 24 24" class="svg-inline" style="color: var(--x-text-gray);"><path d="M19.75 2H4.25C3.01 2 2 3.01 2 4.25v15.5C2 20.99 3.01 22 4.25 22h15.5c1.24 0 2.25-1.01 2.25-2.25V4.25C22 3.01 20.99 2 19.75 2zM4.25 3.5h15.5c.41 0 .75.34.75.75v10.12l-3.21-3.21c-.29-.29-.77-.29-1.06 0l-3.87 3.87-2.31-2.31a.75.75 0 00-1.06 0L3.5 16.5V4.25c0-.41.34-.75.75-.75zM3.5 18.62l5.03-5.03 2.84 2.84c.29.29.77.29 1.06 0l-3.34-3.34 3.77 3.77V19.75c0 .41-.34.75-.75.75H4.25c-.41 0-.75-.34-.75-.75v-1.13zM8.5 11c1.38 0 2.5-1.12 2.5-2.5S9.88 6 8.5 6 6 7.12 6 8.5 7.12 11 8.5 11zm0-3.5c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"/></svg>
            </button>

            <input type="text" v-model="messageInput" placeholder="开始撰写私信..." @keyup.enter="sendMessage" :disabled="!chatStore.connected">
            <button @click="sendMessage" class="btn-send" :disabled="!messageInput.trim() && !chatStore.connected">
              <svg viewBox="0 0 24 24" class="svg-inline"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </div>
        </div>
      </div>

    </div>

    <!-- 个人主页弹窗 -->
    <div v-if="activeProfile" class="modal-backdrop" @click.self="activeProfile = null">
      <div class="modal-card">
        <button class="modal-close" @click="activeProfile = null">✕</button>
        <div class="modal-header">
          <div class="modal-avatar-big">
            <img v-if="isUrl(activeProfile.user.avatar)" :src="activeProfile.user.avatar" class="avatar-img-el" />
            <span v-else-if="activeProfile.user.avatar && activeProfile.user.avatar !== '👤'">{{ activeProfile.user.avatar }}</span>
            <span v-else>{{ activeProfile.user.username[0].toUpperCase() }}</span>
          </div>
          <h2 class="modal-nickname">{{ activeProfile.user.nickname }}</h2>
          <p class="modal-handle">@{{ activeProfile.user.username }}</p>

          <!-- 解除好友控制 -->
          <div v-if="isCurrentFriend && activeProfile.user.username !== authStore.username" style="margin-top: 15px;">
            <button @click="handleDeleteFriend(activeProfile.user.username)" class="btn-profile-delete">
              解除好友关系
            </button>
          </div>

         
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


   <div v-if="showChallengeModal" class="modal-backdrop" @click.self="showChallengeModal = false">
      <div class="modal-card" style="max-width: 480px; max-height: 85vh; padding: 20px; text-align: left;">
        <button class="modal-close" @click="showChallengeModal = false">✕</button>
        <h3 style="margin-top: 0; font-size: 1.2rem; font-weight: 800; text-align: center; color: #db2777;">💘 {{ friendQuiz.title }}</h3>
        <p style="font-size: 0.8rem; color: var(--x-text-gray); text-align: center; margin-bottom: 20px;">答题完毕后，点击提交即可由 AI 计算你们的灵犀指数！</p>
        
        <div class="modal-body" style="flex: 1; overflow-y: auto;">
          <div v-for="(q, idx) in friendQuiz.questions" :key="q.id" class="quiz-setup-item" style="margin-bottom: 20px; border-bottom: 1px solid var(--x-border); padding-bottom: 12px;">
            <p style="font-weight: bold; font-size: 0.95rem; margin: 0 0 10px 0;">Q{{ idx + 1 }}. {{ q.text }}</p>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <label v-for="opt in q.options" :key="opt" style="font-size: 0.85rem; display: flex; align-items: center; gap: 8px; cursor: pointer;">
                <input type="radio" :name="'challenge_q_' + q.id" :value="opt[0]" v-model="challengeAnswers[q.id]" style="width: auto;">
                {{ opt }}
              </label>
            </div>
          </div>
          <button @click="submitChallenge" class="x-btn-dark" style="background: #db2777; color: white; height: 40px;">提交我的答题卡</button>
        </div>
      </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed, watch } from 'vue' 
import { useAuthStore } from '../store/auth'
import { useChatStore } from '../store/chat'  // 💡 全局常驻
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'

const authStore = useAuthStore()
const chatStore = useChatStore()
const showAddModal = ref(false)
const newFriendUsername = ref('')

const friends = ref(chatStore.cachedFriends)
const selectedContact = ref(chatStore.activeContact)
const messageInput = ref('')

const messages = computed(() => chatStore.activeMessages)

const fileInput = ref(null)
const activeProfile = ref(null)
const activeMenuIndex = ref(null)

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
  // 💡 彻底修复的 onMounted：完全删除 connectChat() 运行时崩溃漏洞！
  window.addEventListener('click', closeAllMenus)
})

onUnmounted(() => {
  // 💡 核心修改：当离开聊天页面时，不仅清空 selectedContact，
  // 还要手动通知 Pinia 强行将全局活性活跃窗口设为 null，以便下次进入时 100% 优先展示最清纯的联系人信箱列表！
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
    alert("已复制到剪贴板")
  } catch (err) {
    console.error('复制失败', err)
  }
  activeMenuIndex.value = null
}

const handleRecall = (messageId, index) => {
  activeMenuIndex.value = null
  if (!chatStore.connected || !selectedContact.value) return

  if (!window.confirm("确定要撤回这条消息吗？")) {
    return
  }

  chatStore.sendWebSocketPayload({
    type: "recall",
    to: selectedContact.value,
    message_id: messageId
  })

  chatStore.activeMessages.splice(index, 1, {
    system: true,
    text: '你撤回了一条消息'
  })

  updateLastMessage(selectedContact.value, '你撤回了一条消息', true, '', true)
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
      selectedContact.value = null // 自动退出
      fetchFriends()               // 静默刷新列表
    } else {
      alert('解除好友失败')
    }
  } catch (err) {
    console.error(err)
    alert('请求失败')
  }
}

// 💡 核心升级 B：直接让页面调用全局仓库的 fetchFriends() 写入并共享状态，消灭前端未读重置Bug
const fetchFriends = async () => {
  await chatStore.fetchFriends()
  friends.value = chatStore.cachedFriends
}

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
  
  // 缓存优先
  const cachedHistory = chatStore.cachedHistory[friendUsername] || []
  chatStore.activeMessages = [...cachedHistory]
  scrollToBottom()

  const friend = friends.value.find(f => f.username === friendUsername)
  if (friend) {
    friend.unread = 0
    friends.value = [...friends.value]
    chatStore.setFriends(friends.value)
  }

  chatStore.sendWebSocketPayload({ type: "read", to: friendUsername })

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

const updateLastMessage = (friendUsername, text, isSelf = false, timeStr = '', isSystemNotice = false) => {
  const friend = friends.value.find(f => f.username === friendUsername)
  if (!friend) return

  let displayMsg = text
  if (text.startsWith('data:image/')) {
    displayMsg = '[图片]'
  } else if (!isSystemNotice && text.length > 15) {
    displayMsg = text.substring(0, 15) + '...'
  }

  if (isSystemNotice) {
    friend.last_message = displayMsg
  } else {
    const prefix = isSelf ? '我' : friend.nickname
    friend.last_message = `${prefix}: ${displayMsg}`
  }

  let timeLabel = ""
  if (timeStr) {
    timeLabel = timeStr.split(' ')[1] || ""
  } else {
    const now = new Date()
    timeLabel = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  }
  friend.last_message_time = timeLabel
  
  friends.value = [...friends.value]
  chatStore.setFriends(friends.value)
}

const sendMessage = () => {
  if (!chatStore.connected || !selectedContact.value) return
  const text = messageInput.value.trim()
  if (!text) return

  chatStore.sendWebSocketPayload({
    type: "msg",
    to: selectedContact.value,
    message: text
  })
  
  chatStore.activeMessages.push({ 
    id: null,
    from: authStore.username, 
    text: text, 
    time: getCurrentTimeLabel(), 
    self: true, 
    system: false,
    is_read: false 
  })
  
  updateLastMessage(selectedContact.value, text, true)
  chatStore.setHistory(selectedContact.value, [...chatStore.activeMessages])

  messageInput.value = ''
  scrollToBottom()
}

const friendQuiz = ref(null) // 记录对方的测验信息
const showChallengeModal = ref(false)
const challengeAnswers = reactive({}) // 存储挑战者的答案

// 在您原本的 openUserProfile 函数中，追加对好友测验的加载：
const openUserProfile = async (targetUsername) => {
  try {
    // 1. 纯净流：只拉取用户资料与用户动态，彻底删除对 /quiz 的调用
    const [profileRes, postsRes] = await Promise.all([
      apiFetch(`/auth/profile/${targetUsername}`),
      apiFetch(`/moments/user/${targetUsername}`)
    ])
    
    // 2. 仅校验这两者的状态
    if (profileRes.ok && postsRes.ok) {
      const user = await profileRes.json()
      const userPosts = await postsRes.json()
      
      // 装载弹窗
      activeProfile.value = {
        user: user,
        posts: userPosts.moments
      }
    } else {
      alert('加载用户数据失败')
    }
  } catch (err) {
    console.error('加载主页异常:', err)
    alert('无法加载该用户的主页')
  }
}

// 开启答题挑战
const startChallenge = () => {
  if (!friendQuiz.value) return
  // 初始化挑战答案，默认选A
  friendQuiz.value.questions.forEach(q => {
    challengeAnswers[q.id] = 'A'
  })
  showChallengeModal.value = true
}

// 提交答题卡并计算默契度
const submitChallenge = async () => {
  const payload = {
    quiz_id: friendQuiz.value.quiz_id,
    answers: challengeAnswers
  }
  try {
    const res = await apiFetch('/quiz/submit', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    const data = await res.json()
    if (res.ok) {
      // 成功后，关闭答题弹窗，手动将最新得分展示在个人主页上（0ms交互）
      showChallengeModal.value = false
      friendQuiz.value.already_challenged = true
      friendQuiz.value.score = data.score
      
      // 庆祝彩蛋
      alert(`🎉 答题成功！你们的默契度高达: ${data.score}%！\n答对题数: ${data.correct_count}/${data.total_questions}`)
    }
  } catch {
    alert('提交答题失败')
  }
}

const triggerImageSelect = () => {
  if (fileInput.value) { fileInput.value.click() }
}

const handleImageUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 1. 限制文件上传大小为 2MB 
  if (file.size > 2 * 1024 * 1024) {
    alert("图片过大，限制上传小于 2MB 的图片。")
    event.target.value = ""
    return
  }

  // 2. 💡 核心优化 A：选择图片需要确认。利用 HTML5 的 ObjectURL 机制零延迟本地生成预览
  const localPreviewUrl = URL.createObjectURL(file)
  
  // 弹出安全确认框
  if (!window.confirm("确定要向对方发送选择的这张图片吗？")) {
    URL.revokeObjectURL(localPreviewUrl) 
    event.target.value = "" 
    return
  }

  try {
    // 3. 💡 核心优化 B：利用标准的 HTTP FormData 发起文件上传
    const formData = new FormData()
    formData.append("file", file)

    // 调用我们在上一步重构的 apiFetch，自动携带 JWT 并支持上传
    const res = await apiFetch("/chat/upload", {
      method: "POST",
      body: formData 
    })
    const data = await res.json()

    if (res.ok && data.success) {
      // 💡 升级：自适应识别：如果后端传回的是 http/https 开头的绝对云地址直接使用，否则再使用 API_BASE 拼接
      const imageUrl = data.url.startsWith('http') ? data.url : `${API_BASE}${data.url}`

      // 通过 WebSocket 发送短 URL 链接
      chatStore.sendWebSocketPayload({
        type: "msg",
        to: selectedContact.value,
        message: imageUrl
      })

      // 本地追加渲染
      chatStore.activeMessages.push({
        id: null,
        from: authStore.username,
        text: imageUrl,
        time: getCurrentTimeLabel(),
        self: true,
        system: false,
        is_read: false
      })

      // 同步刷新左侧卡片显示为 [图片]
      chatStore.updateLastMessageState(selectedContact.value, '[图片]', true)
      chatStore.setHistory(selectedContact.value, [...chatStore.activeMessages])
    } else {
      alert(data.detail || "图片上传失败")
    }
  } catch (err) {
    console.error(err)
    alert("上传图片过程中发生网络故障")
  } finally {
    URL.revokeObjectURL(localPreviewUrl) 
    event.target.value = "" 
  }
}

const isImage = (text) => {
  if (!text) return false
  return text.startsWith('data:image/') || text.match(/\.(jpeg|jpg|gif|png|webp)$/i) != null
}

const isUrl = (text) => {
  if (!text) return false
  return text.startsWith('http://') || text.startsWith('https://') || text.startsWith('/')
}

const scrollToBottom = () => {
  nextTick(() => {
    const flow = document.getElementById('chatFlow')
    if (flow) {
      flow.scrollTop = flow.scrollHeight
    }
  })
}

const getCurrentTimeLabel = () => {
  const now = new Date()
  return `${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}
</script>






<style scoped>
/* 𝕏 经典分栏排版 */
.x-dm-layout {
  display: flex;
  height: calc(100vh - 106px);
  width: 100%;
}
@media (min-width: 768px) {
  .x-dm-layout { height: calc(100vh - 24px); }
}

/* 左侧联系人列表 */
.contacts-sidebar {
  width: 100%;
  border-right: 1px solid var(--x-border);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}
.sidebar-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px; border-bottom: 1px solid var(--x-border);
}
.btn-icon { background: transparent; border: none; cursor: pointer; color: var(--x-blue); display: flex; align-items: center; }
.svg-inline { width: 22px; height: 22px; fill: currentColor; }

.add-friend-panel {
  display: flex; gap: 8px; padding: 12px 16px; border-bottom: 1px solid var(--x-border); background: #f7f9fa;
}
.add-friend-panel input {
  flex: 1; padding: 6px 12px; border: 1px solid var(--x-border); border-radius: 9999px; outline: none; font-size: 0.9rem;
}
.x-btn-pill {
  background: #0f1419; color: white; border: none; padding: 0 16px; border-radius: 9999px; font-weight: bold; cursor: pointer;
}

.contacts-list { flex: 1; overflow-y: auto; }
.no-contacts { padding: 30px; text-align: center; color: var(--x-text-gray); font-size: 0.9rem; line-height: 1.5; }
.contact-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px;
  border-bottom: 1px solid var(--x-border); cursor: pointer; transition: background 0.2s;
}
.contact-item:hover { background: var(--x-bg-hover); }
.contact-item.active { background: #f0f3f4; }

/* 响应式名片行布局 */
.contact-details-row {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden; /* 防止溢出撑开 */
}
.contact-details { display: flex; flex-direction: column; text-align: left; overflow: hidden; flex: 1; }
.contact-name-row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.contact-name { font-weight: bold; font-size: 0.95rem; color: var(--x-text-main); }
.contact-time-sub { font-size: 0.75rem; color: var(--x-text-gray); margin-left: 8px; }

/* 最新消息单行截取 */
.contact-last-msg {
  font-size: 0.8rem;
  color: var(--x-text-gray);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* 文字超宽自动打点 */
  margin-top: 2px;
  text-align: left;
}

/* 亮红色未读数徽章 */
.unread-badge {
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
  animation: pop-scale 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes pop-scale {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}

/* 极简头像，细框 */
.contact-avatar {
  width: 38px; height: 38px;
  background: #ffffff;
  border: 1px solid var(--x-border);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 1.1rem; color: var(--x-text-gray);
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.2s;
}
.contact-avatar:hover { border-color: var(--x-blue); }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }

/* 右侧聊天主窗口 */
.chat-main { width: 100%; display: flex; flex-direction: column; }
.welcome-box { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; padding: 24px; }

.chat-window { display: flex; flex-direction: column; height: 100%; }
.chat-header {
  display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid var(--x-border);
}
.chat-header-left { display: flex; align-items: center; gap: 12px; }
.btn-back { background: transparent; border: none; cursor: pointer; color: var(--x-text-main); display: flex; align-items: center; }
.header-info { display: flex; flex-direction: column; }
.header-name { font-weight: bold; font-size: 0.95rem; }
.header-status { font-size: 0.8rem; color: var(--x-text-gray); }
.btn-reconnect {
  background: var(--x-blue); color: white; border: none; font-size: 0.8rem;
  font-weight: bold; padding: 4px 12px; border-radius: 9999px; cursor: pointer;
}

.chat-body { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; background: white; }
.message-row { display: flex; width: 100%; }
.self-row { justify-content: flex-end; }
.peer-row { justify-content: flex-start; }
.sys-row { justify-content: center; }

/* 气泡修剪 */
.msg-bubble {
  max-width: 70%; padding: 10px 14px; font-size: 0.95rem; line-height: 1.4; word-wrap: break-word; 
  position: relative; 
  cursor: pointer;
  user-select: none; 
}
.self-row .msg-bubble { background: var(--x-blue); color: white; border-radius: 18px 18px 2px 18px; }
.peer-row .msg-bubble { background: #eff3f4; color: var(--x-text-main); border-radius: 18px 18px 18px 2px; }

/* 消息元数据 */
.msg-meta {
  display: flex; align-items: center; justify-content: flex-end; gap: 6px; margin-top: 4px; font-size: 0.7rem;
}
.read-status { opacity: 0.6; color: #fca5a5; font-weight: bold; } 
.read-status.status-read { color: #a7f3d0; opacity: 0.8; }        
.msg-time { display: block; opacity: 0.7; text-align: right; }

/* 对方发送的消息不展示已读状态 */
.peer-row .read-status { display: none !important; }
.peer-row .msg-meta { justify-content: flex-end; }
.peer-row .msg-time { color: var(--x-text-gray); }

/* Telegram 风格气泡操作菜单样式 */
.telegram-menu {
  position: absolute;
  bottom: calc(100% + 4px); /* 悬浮在消息气泡上方 */
  background: rgba(15, 20, 25, 0.96); /* 𝕏 经典深邃蓝黑 */
  backdrop-filter: blur(12px);
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
  padding: 6px;
  z-index: 210;
  display: flex;
  flex-direction: column;
  min-width: 120px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  animation: pop-menu 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.15);
}
@keyframes pop-menu {
  0% { transform: scale(0.9) translateY(5px); opacity: 0; }
  100% { transform: scale(1) translateY(0); opacity: 1; }
}
/* 左右对齐微调 */
.self-row .telegram-menu { right: 8px; transform-origin: bottom right; }
.peer-row .telegram-menu { left: 8px; transform-origin: bottom left; }

.menu-item {
  background: transparent;
  border: none;
  padding: 10px 14px;
  text-align: left;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  color: #ffffff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: background 0.15s;
}
.menu-item:hover { background: rgba(255, 255, 255, 0.1); }
.menu-icon { width: 16px; height: 16px; fill: currentColor; }
.menu-divider { height: 1px; background: rgba(255, 255, 255, 0.08); margin: 4px 6px; }
.menu-item.delete-btn { color: #ff4d4f; }
.menu-item.delete-btn:hover { background: rgba(255, 77, 79, 0.15); }

/* 系统灰色提示 */
.sys-notice {
  font-size: 0.8rem;
  color: var(--x-text-gray);
  background: #f7f9fa;
  padding: 4px 14px;
  border-radius: 9999px;
  font-style: italic; 
}

.chat-img {
  max-width: 100%; max-height: 220px; border-radius: 12px; display: block; margin-top: 4px; cursor: pointer;
}

.chat-footer { padding: 12px 16px; border-top: 1px solid var(--x-border); }
.input-pill { display: flex; align-items: center; background: #f7f9fa; border-radius: 9999px; padding: 4px 14px; gap: 8px; }
.input-pill input { flex: 1; border: none; background: transparent; outline: none; font-size: 0.95rem; height: 32px; }
.btn-send { background: transparent; border: none; cursor: pointer; display: flex; align-items: center; color: var(--x-blue); }
.btn-send:disabled { color: var(--x-text-gray); cursor: not-allowed; }

/* 个人主页弹窗 (Profile) */
.modal-backdrop {
  position: fixed; top: 0; bottom: 0; left: 0; right: 0;
  background: rgba(0, 0, 0, 0.4); display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-card {
  width: 90%; max-width: 450px; background: white; border-radius: 20px;
  max-height: 80vh; display: flex; flex-direction: column; overflow: hidden; position: relative;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.modal-close {
  position: absolute; top: 16px; right: 16px; background: transparent;
  border: none; font-size: 1.25rem; font-weight: bold; cursor: pointer; color: var(--x-text-gray);
}
.modal-header { padding: 30px 24px 16px 24px; text-align: center; border-bottom: 1px solid var(--x-border); }
.modal-avatar-big {
  width: 70px; height: 70px; background: #eff3f4; border-radius: 50%; font-size: 2.5rem;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto;
}
.modal-nickname { margin: 0; font-size: 1.25rem; font-weight: 800; }
.modal-handle { margin: 4px 0 0 0; color: var(--x-text-gray); font-size: 0.9rem; }

.modal-body { flex: 1; overflow-y: auto; padding: 16px 24px; }
.modal-tab-title { font-size: 1rem; font-weight: 800; border-bottom: 2px solid var(--x-blue); padding-bottom: 6px; margin: 0 0 12px 0; display: inline-block;}
.no-posts-hint { text-align: center; color: var(--x-text-gray); font-size: 0.9rem; padding: 24px 0; }
.modal-tweet { padding: 12px 0; border-bottom: 1px solid var(--x-border); text-align: left; }
.modal-tweet-time { font-size: 0.8rem; color: var(--x-text-gray); margin-bottom: 4px; }
.modal-tweet-content { font-size: 0.95rem; line-height: 1.4; word-wrap: break-word;}

/* 双端自适应 */
@media (max-width: 767px) {
  .contacts-sidebar.hide-on-mobile { display: none !important; }
  .chat-main.hide-on-mobile { display: none !important; }
  .btn-back { display: block !important; }
}
@media (min-width: 768px) {
  .contacts-sidebar { width: 280px; }
  .chat-main { flex: 1; }
  .btn-back { display: none !important; }
}

.btn-profile-delete {
  background: transparent;
  color: #ef4444;
  border: 1px solid #fca5a5;
  font-weight: bold;
  font-size: 0.85rem;
  padding: 0 16px;
  height: 32px;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-profile-delete:hover {
  background: #fee2e2;
  border-color: #ef4444;
}
</style>