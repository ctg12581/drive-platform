// src/store/chat.js
// 全局聊天状态：好友列表、历史消息缓存、常驻 WebSocket 与未读数。
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { readJSON, writeJSON, isImageUrl, isTokenExpired } from '@drive/shared'
import { useAuthStore } from './auth'
import { apiFetch, buildChatWsUrl } from '../utils/api'

// 好友申请改为服务端 WS 推送；这里的轮询仅作“断线期间”的低频兜底
const PENDING_POLL_INTERVAL = 60000
// 断线重连：指数退避（1s 起，最长 30s），并加抖动避免多端同时重连打爆后端
const RECONNECT_BASE_DELAY = 1000
const RECONNECT_MAX_DELAY = 30000
// 心跳：每 25s 发一次 ping；服务端支持 pong 时，10s 内没回就判定连接已死
const HEARTBEAT_INTERVAL = 25000
const HEARTBEAT_TIMEOUT = 10000

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
  // 连接建立/回到前台时自增，聊天页据此补拉当前会话历史
  const resyncTick = ref(0)

  let pendingPollTimer = null
  let reconnectTimer = null
  let manualClose = false
  let reconnectAttempts = 0
  let heartbeatTimer = null
  let pongTimeoutTimer = null
  let wakeUpBound = false
  let hasConnectedOnce = false
  let serverSupportsPong = false
  let lastWakeSyncAt = 0

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

  function notifyFriendRequestsChanged() {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('chat:friend-requests-changed'))
    }
  }

  function stopPendingPoll() {
    if (pendingPollTimer) {
      clearInterval(pendingPollTimer)
      pendingPollTimer = null
    }
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    if (pongTimeoutTimer) {
      clearTimeout(pongTimeoutTimer)
      pongTimeoutTimer = null
    }
  }

  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (!ws.value || !connected.value) return
      sendWebSocketPayload({ type: 'ping' })
      if (pongTimeoutTimer) clearTimeout(pongTimeoutTimer)
      pongTimeoutTimer = setTimeout(() => {
        // 老服务端不支持 pong 时不误判；确认支持后再以“无 pong”判定半开连接
        if (!serverSupportsPong) return
        console.warn('聊天心跳超时，主动断开以触发重连')
        try {
          if (ws.value) ws.value.close()
        } catch {
          /* ignore */
        }
      }, HEARTBEAT_TIMEOUT)
    }, HEARTBEAT_INTERVAL)
  }

  function scheduleReconnect() {
    if (reconnectTimer || manualClose || !authStore.isLoggedIn) return
    const attempt = reconnectAttempts++
    const base = Math.min(RECONNECT_MAX_DELAY, RECONNECT_BASE_DELAY * 2 ** attempt)
    // 抖动：80%~120%，避免多端同时重连
    const delay = Math.round(base * (0.8 + Math.random() * 0.4))
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connectWebSocket()
    }, delay)
  }

  // 回到前台 / 网络恢复：连接没了就重连；还在连接就触发一次补偿拉取，防止后台漏收
  function handleWakeUp() {
    if (typeof document !== 'undefined' && document.hidden) return
    if (!authStore.isLoggedIn) return
    if (!ws.value) {
      connectWebSocket()
    } else if (connected.value) {
      // 20s 内只补偿一次，避免频繁切标签页造成重复请求
      const now = Date.now()
      if (now - lastWakeSyncAt < 20000) return
      lastWakeSyncAt = now
      fetchFriends()
      fetchPendingRequestsCount()
      resyncTick.value++
    }
  }

  function bindWakeUpListeners() {
    if (wakeUpBound || typeof window === 'undefined') return
    wakeUpBound = true
    window.addEventListener('online', handleWakeUp)
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', handleWakeUp)
    }
  }

  function connectWebSocket() {
    if (!authStore.username || ws.value) return
    bindWakeUpListeners()

    // token 已过期就没必要再连（否则会陷入无效重连），直接登出
    if (authStore.token && isTokenExpired(authStore.token)) {
      manualClose = true
      authStore.logout()
      return
    }

    manualClose = false
    ws.value = new WebSocket(buildChatWsUrl(authStore.username))

    ws.value.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
      serverSupportsPong = false
      startHeartbeat()
      fetchPendingRequestsCount()
      fetchFriends()
      stopPendingPoll()
      pendingPollTimer = setInterval(() => {
        // 连接正常时由服务端推送好友申请，无需轮询；仅在断线时低频兜底
        if (!connected.value) fetchPendingRequestsCount()
      }, PENDING_POLL_INTERVAL)
      if (activeContact.value) {
        sendWebSocketPayload({ type: 'read', to: activeContact.value })
      }
      // 非首次连接（重连）成功后，通知聊天页补拉当前会话历史，防止断线期间漏消息
      if (hasConnectedOnce) {
        resyncTick.value++
      } else {
        hasConnectedOnce = true
      }
    }

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // 心跳应答：证明连接仍然存活
      if (data.type === 'pong') {
        serverSupportsPong = true
        if (pongTimeoutTimer) {
          clearTimeout(pongTimeoutTimer)
          pongTimeoutTimer = null
        }
        return
      }

      // 好友申请 / 关系变化：服务端主动推送，实时更新未读数与列表（替代轮询）
      if (
        data.type === 'friend_request' ||
        data.type === 'friend_accept' ||
        data.type === 'friend_update'
      ) {
        fetchPendingRequestsCount()
        if (data.type !== 'friend_request') fetchFriends()
        notifyFriendRequestsChanged()
        return
      }

      // 有新动态发布：通知首页更新“新动态”气泡（替代首页 15s 轮询）
      if (data.type === 'new_moments') {
        if (typeof window !== 'undefined') {
          window.dispatchEvent(
            new CustomEvent('moments:new', { detail: Number(data.count) || 1 }),
          )
        }
        return
      }

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

    ws.value.onclose = (event) => {
      connected.value = false
      ws.value = null
      stopHeartbeat()
      stopPendingPoll()
      // 1008：鉴权/策略失败（如 token 失效），重连无法恢复，直接登出停止重连
      if (event && event.code === 1008) {
        manualClose = true
        authStore.logout()
        return
      }
      if (!manualClose) {
        scheduleReconnect()
      }
    }
  }

  function disconnectWebSocket() {
    manualClose = true
    reconnectAttempts = 0
    stopHeartbeat()
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
    resyncTick,
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
