// src/store/chat.js
// 全局聊天状态：好友列表、历史消息缓存、常驻 WebSocket 与未读数。
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { readJSON, writeJSON, isImageUrl } from '@drive/shared'
import { useAuthStore } from './auth'
import { apiFetch, buildChatWsUrl } from '../utils/api'

const PENDING_POLL_INTERVAL = 20000
const RECONNECT_DELAY = 5000

// localStorage 写入防抖：高频聊天时避免每次都同步序列化整个缓存对象
const writeTimers = {}
function debouncedWrite(key, value, delay = 300) {
  if (writeTimers[key]) clearTimeout(writeTimers[key])
  writeTimers[key] = setTimeout(() => {
    writeJSON(key, value)
    delete writeTimers[key]
  }, delay)
}

// 提示音复用同一个 AudioContext，避免每条消息都新建实例耗尽资源
let notificationAudioCtx = null
function getNotificationAudioCtx() {
  if (notificationAudioCtx) return notificationAudioCtx
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return null
  notificationAudioCtx = new AudioCtx()
  return notificationAudioCtx
}

export const useChatStore = defineStore('chat', () => {
  const authStore = useAuthStore()

  // ---- 本地缓存（刷新页面后 0ms 恢复）----
  const cachedFriends = ref(readJSON('cached_friends', []))
  const cachedHistory = ref(readJSON('cached_history', {}))
  const activeContact = ref(localStorage.getItem('active_contact') || null)

  // ---- 运行时状态 ----
  const ws = ref(null)
  const connected = ref(false)
  const activeMessages = ref([])
  const pendingRequestsCount = ref(0)

  let pendingPollTimer = null
  let reconnectTimer = null
  let manualClose = false

  const totalUnreadCount = computed(() =>
    cachedFriends.value.reduce((sum, friend) => sum + (friend.unread || 0), 0),
  )

  function setFriends(friends) {
    cachedFriends.value = friends
    debouncedWrite('cached_friends', friends)
  }

  function setHistory(friendUsername, history) {
    cachedHistory.value[friendUsername] = history.slice(-30)
    debouncedWrite('cached_history', cachedHistory.value)
  }

  function setActiveContact(contact) {
    activeContact.value = contact
    if (contact) {
      localStorage.setItem('active_contact', contact)
    } else {
      localStorage.removeItem('active_contact')
    }
  }

  async function fetchFriends() {
    if (!authStore.isLoggedIn) return
    try {
      const res = await apiFetch('/chat/friends')
      const data = await res.json()
      if (res.ok) {
        setFriends(data.friends)
      }
    } catch (err) {
      console.error('全局获取好友列表异常:', err)
    }
  }

  async function fetchPendingRequestsCount() {
    if (!authStore.isLoggedIn) return
    if (typeof document !== 'undefined' && document.hidden) return
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

  function stopPendingPoll() {
    if (pendingPollTimer) {
      clearInterval(pendingPollTimer)
      pendingPollTimer = null
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer || manualClose || !authStore.isLoggedIn) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connectWebSocket()
    }, RECONNECT_DELAY)
  }

  function connectWebSocket() {
    if (!authStore.username || ws.value) return

    manualClose = false
    ws.value = new WebSocket(buildChatWsUrl(authStore.username))

    ws.value.onopen = () => {
      connected.value = true
      fetchPendingRequestsCount()
      fetchFriends()
      stopPendingPoll()
      pendingPollTimer = setInterval(fetchPendingRequestsCount, PENDING_POLL_INTERVAL)
      if (activeContact.value) {
        sendWebSocketPayload({ type: 'read', to: activeContact.value })
      }
    }

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // 服务端确认消息已落库：回填真实 id，使刚发出的消息也能撤回
      if (data.type === 'msg_ack') {
        const idx = activeMessages.value.findIndex(
          (m) => m.client_id && m.client_id === data.client_id,
        )
        if (idx !== -1) {
          activeMessages.value[idx].id = data.id
          if (activeContact.value) setHistory(activeContact.value, [...activeMessages.value])
        }
        return
      }

      if (data.type === 'error') {
        console.warn('聊天发送失败:', data.message)
        return
      }

      if (data.type === 'read') {
        if (activeContact.value === data.from) {
          activeMessages.value.forEach((msg) => {
            if (msg.self) msg.is_read = true
          })
          setHistory(activeContact.value, [...activeMessages.value])
        }
        return
      }

      if (data.type === 'recall') {
        const recalledId = data.message_id
        if (activeContact.value === data.from) {
          const msgIndex = activeMessages.value.findIndex((m) => m.id === recalledId)
          if (msgIndex !== -1) {
            activeMessages.value.splice(msgIndex, 1, {
              system: true,
              text: '对方撤回了一条消息',
            })
            setHistory(activeContact.value, [...activeMessages.value])
          }
        } else {
          const hist = cachedHistory.value[data.from] || []
          const msgIndex = hist.findIndex((m) => m.id === recalledId)
          if (msgIndex !== -1) {
            hist.splice(msgIndex, 1, { system: true, text: '对方撤回了一条消息' })
            setHistory(data.from, hist)
          }
        }
        updateLastMessageState(data.from, '对方撤回了一条消息', false, '', true)
        return
      }

      const isMsg = !data.type || data.type === 'msg'
      if (isMsg) {
        playNotificationSound()
        if (activeContact.value === data.from) {
          activeMessages.value.push({
            id: data.id,
            from: data.from,
            text: data.message,
            time: getCurrentTimeLabel(),
            self: false,
            system: false,
            is_read: true,
          })
          setHistory(activeContact.value, [...activeMessages.value])
          sendWebSocketPayload({ type: 'read', to: data.from })
        } else {
          const friend = cachedFriends.value.find((f) => f.username === data.from)
          if (friend) {
            friend.unread = (friend.unread || 0) + 1
            setFriends([...cachedFriends.value])
          } else {
            fetchFriends()
          }
        }
        updateLastMessageState(data.from, data.message, false)
      }
    }

    ws.value.onclose = () => {
      connected.value = false
      ws.value = null
      stopPendingPoll()
      if (!manualClose) {
        scheduleReconnect()
      }
    }
  }

  function disconnectWebSocket() {
    manualClose = true
    stopPendingPoll()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
  }

  function sendWebSocketPayload(payload) {
    if (ws.value && connected.value) {
      ws.value.send(JSON.stringify(payload))
    }
  }

  function updateLastMessageState(friendUsername, text, isSelf = false, timeStr = '', isSystemNotice = false) {
    const friend = cachedFriends.value.find((f) => f.username === friendUsername)
    if (!friend) return

    let displayMsg = text
    if (isImageUrl(text)) {
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

    const timeLabel = timeStr
      ? timeStr.split(' ')[1] || ''
      : new Date().toISOString()
    friend.last_message_time = timeLabel

    setFriends([...cachedFriends.value])
  }

  function playNotificationSound() {
    try {
      const audioCtx = getNotificationAudioCtx()
      if (!audioCtx) return
      if (audioCtx.state === 'suspended') {
        const resume = () => {
          audioCtx.resume().then(() => playSynthPing(audioCtx))
          window.removeEventListener('click', resume)
        }
        window.addEventListener('click', resume, { once: true })
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
    cachedFriends,
    cachedHistory,
    activeContact,
    ws,
    connected,
    activeMessages,
    totalUnreadCount,
    pendingRequestsCount,
    setFriends,
    setHistory,
    setActiveContact,
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketPayload,
    updateLastMessageState,
    fetchFriends,
  }
})
