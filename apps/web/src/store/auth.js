// src/store/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 💡 辅助函数：在本地解析并计算 JWT Token 是否在数学上已过期
function isTokenExpired(token) {
  if (!token) return true
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    const payload = JSON.parse(jsonPayload)
    
    // 获取当前时间戳（秒）进行对比
    const now = Math.floor(Date.now() / 1000)
    return payload.exp < now
  } catch (e) {
    return true // 如果解析失败，默认视为已过期
  }
}

export const useAuthStore = defineStore('auth', () => {
  const savedToken = localStorage.getItem('drive_token') || ''
  const savedUser = localStorage.getItem('drive_username') || ''
  const savedNickname = localStorage.getItem('drive_nickname') || ''
  const savedAvatar = localStorage.getItem('drive_avatar') || '👤'

  // 响应式状态声明
  const token = ref(savedToken)
  const username = ref(savedUser)
  const nickname = ref(savedNickname)
  const avatar = ref(savedAvatar)

  // 💡 静态保险：初始化时自检。如果发现本地 Token 已过期，直接静默执行注销清除
  if (token.value && isTokenExpired(token.value)) {
    token.value = ''
    username.value = ''
    nickname.value = ''
    avatar.value = '👤'
    localStorage.removeItem('drive_token')
    localStorage.removeItem('drive_username')
    localStorage.removeItem('drive_nickname')
    localStorage.removeItem('drive_avatar')
    console.warn("🔐 安全自检：本地登录凭证已过期，已被安全擦除")
  }

  const isLoggedIn = computed(() => !!token.value)

  function setLogin(newToken, newUser, newNickname = '', newAvatar = '👤') {
    token.value = newToken
    username.value = newUser
    nickname.value = newNickname || newUser
    avatar.value = newAvatar || '👤'
    
    localStorage.setItem('drive_token', newToken)
    localStorage.setItem('drive_username', newUser)
    localStorage.setItem('drive_nickname', nickname.value)
    localStorage.setItem('drive_avatar', avatar.value)
  }

  function updateProfileState(newNickname, newAvatar) {
    nickname.value = newNickname
    avatar.value = newAvatar
    localStorage.setItem('drive_nickname', newNickname)
    localStorage.setItem('drive_avatar', newAvatar)
  }

  function logout() {
    token.value = ''
    username.value = ''
    nickname.value = ''
    avatar.value = '👤'
    localStorage.removeItem('drive_token')
    localStorage.removeItem('drive_username')
    localStorage.removeItem('drive_nickname')
    localStorage.removeItem('drive_avatar')
  }

  return { token, username, nickname, avatar, isLoggedIn, setLogin, updateProfileState, logout }
})