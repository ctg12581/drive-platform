// src/store/chat.js (完整订正无错版代码)
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'
import { formatLocalTime } from '../utils/date'
import { apiFetch } from '../utils/api'

export const useChatStore = defineStore('chat', () => {
  const authStore = useAuthStore()
  
  const cachedFriends = ref(JSON.parse(localStorage.getItem('cached_friends') || '[]'))
  const cachedHistory = ref(JSON.parse(localStorage.getItem('cached_history') || '{}'))
  const activeContact = ref(localStorage.getItem('active_contact') || null)

  // 全局唯一的常驻 WebSocket 实例
  const ws = ref(null)
  const connected = ref(false)
  const activeMessages = ref([])

  // 全站未读消息总和
  const totalUnreadCount = computed(() => {
    return cachedFriends.value.reduce((sum, friend) => sum + (friend.unread || 0), 0)
  })

  // 待审批的好友申请数量
  const pendingRequestsCount = ref(0)

  function setFriends(friends) {
    cachedFriends.value = friends
    localStorage.setItem('cached_friends', JSON.stringify(friends))
  }

  function setHistory(friendUsername, history) {
    cachedHistory.value[friendUsername] = history.slice(-30)
    localStorage.setItem('cached_history', JSON.stringify(cachedHistory.value))
  }

  function setActiveContact(contact) {
    activeContact.value = contact
    if (contact) {
      localStorage.setItem('active_contact', contact)
    } else {
      localStorage.removeItem('active_contact')
    }
  }

  // 💡 命名修复：将 fetchFriendsGlobal 重新统一对齐命名为 fetchFriends
  async function fetchFriends() {
    if (!authStore.isLoggedIn) return
    try {
      const res = await apiFetch('/chat/friends')
      const data = await res.json()
      if (res.ok) {
        // 严格遵循并信任后端的数据库精准未读数
        setFriends(data.friends)
      }
    } catch (err) {
      console.error('全局获取好友列表异常:', err)
    }
  }

  // 获取待审批好友申请数
  async function fetchPendingRequestsCount() {
    if (!authStore.isLoggedIn) return
    try {
      const res = await apiFetch('/chat/friend-requests/pending')
      const data = await res.json()
      if (res.ok) {
        pendingRequestsCount.value = data.requests.length
      }
    } catch {
      console.error('获取通知未读数异常')
    }
  }

  // 全局常驻 WebSocket
  function connectWebSocket() {
    const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://127.0.0.1:3000'
    if (!authStore.username || ws.value) return

    ws.value = new WebSocket(`${WS_BASE}/chat/ws/${authStore.username}`)

    ws.value.onopen = () => {
      connected.value = true
      fetchPendingRequestsCount()
      // 连接成功后，也静默拉取一次最新好友列表与未读数
      fetchFriends() 
      // 每 20 秒一次的待批准通知长轮询
      setInterval(fetchPendingRequestsCount, 20000)
      if (activeContact.value) {
        sendWebSocketPayload({ type: "read", to: activeContact.value })
      }
    }

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      playNotificationSound()

      // 1. 已读回执
      if (data.type === 'read') {
        if (activeContact.value === data.from) {
          activeMessages.value.forEach(msg => {
            if (msg.self) msg.is_read = true
          })
          setHistory(activeContact.value, [...activeMessages.value])
        }
        return
      }

      // 2. 撤回回执
      if (data.type === 'recall') {
        const recalledId = data.message_id
        if (activeContact.value === data.from) {
          const msgIndex = activeMessages.value.findIndex(m => m.id === recalledId)
          if (msgIndex !== -1) {
            activeMessages.value.splice(msgIndex, 1, {
              system: true,
              text: '对方撤回了一条消息'
            })
            setHistory(activeContact.value, [...activeMessages.value])
          }
        } else {
          const hist = cachedHistory.value[data.from] || []
          const msgIndex = hist.findIndex(m => m.id === recalledId)
          if (msgIndex !== -1) {
            hist.splice(msgIndex, 1, { system: true, text: '对方撤回了一条消息' })
            setHistory(data.from, hist)
          }
        }
        updateLastMessageState(data.from, '对方撤回了一条消息', false, '', true)
        return
      }

      // 3. 普通实时消息
      const isMsg = !data.type || data.type === 'msg'
      if (isMsg) {
        if (activeContact.value === data.from) {
          // 如果用户当前正好在跟发送人热聊中：直接塞入活跃会话流并自动已读
          activeMessages.value.push({
            id: data.id,
            from: data.from,
            text: data.message,
            time: getCurrentTimeLabel(),
            self: false,
            system: false,
            is_read: true 
          })
          setHistory(activeContact.value, [...activeMessages.value])
          sendWebSocketPayload({ type: "read", to: data.from })
        } else {
          // 如果没开对话框
          const friend = cachedFriends.value.find(f => f.username === data.from)
          if (friend) {
            friend.unread = (friend.unread || 0) + 1
            setFriends([...cachedFriends.value])
          } else {
            // 💡 容灾：如果是全新好友（或者本地缓存没有此人），立刻重新拉取一次好友列表
            fetchFriends() 
          }
        }
        updateLastMessageState(data.from, data.message, false)
      }
    }

    ws.value.onclose = () => {
      connected.value = false
      ws.value = null
      if (authStore.isLoggedIn) {
        setTimeout(connectWebSocket, 5000)
      }
    }
  }

  function disconnectWebSocket() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      connected.value = false
    }
  }

  // 统一通过常驻 WebSocket 实例向后端发送数据
  function sendWebSocketPayload(payload) {
    if (ws.value && connected.value) {
      ws.value.send(JSON.stringify(payload))
    }
  }

 function updateLastMessageState(friendUsername, text, isSelf = false, timeStr = '', isSystemNotice = false) {
        const friend = cachedFriends.value.find(f => f.username === friendUsername)
        if (!friend) return

        let displayMsg = text
        
        // 💡 核心修复：更新图片的正则判定，支持 data:image/ 前缀和标准的 R2 云图片链接后缀
        const isImg = text.startsWith('data:image/') || text.match(/\.(jpeg|jpg|gif|png|webp)/i) != null
        
        if (isImg) {
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
        
        setFriends([...cachedFriends.value])
      }



  function playNotificationSound() {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext
      const audioCtx = new AudioContextClass()
      if (audioCtx.state === 'suspended') {
        const resume = () => {
          audioCtx.resume().then(() => {
            playSynthPing(audioCtx)
            window.removeEventListener('click', resume)
          })
        }
        window.addEventListener('click', resume)
        return
      }
      playSynthPing(audioCtx)
    } catch (err) {
      console.warn('音效拦截:', err)
    }
  }

  function playSynthPing(audioCtx) {
    const osc = audioCtx.createOscillator()
    const gainNode = audioCtx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(520, audioCtx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.08)
    gainNode.gain.setValueAtTime(0.12, audioCtx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25)
    osc.connect(gainNode)
    gainNode.connect(audioCtx.destination)
    osc.start()
    osc.stop(audioCtx.currentTime + 0.25)
  }

  function getCurrentTimeLabel() {
    const now = new Date()
    return `${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  }

  return { 
    cachedFriends, cachedHistory, activeContact, ws, connected, activeMessages, totalUnreadCount, pendingRequestsCount,
    setFriends, setHistory, setActiveContact, connectWebSocket, disconnectWebSocket, sendWebSocketPayload, updateLastMessageState, fetchFriends
  }
})