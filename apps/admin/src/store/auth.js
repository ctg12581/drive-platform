// src/store/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 解析并验证管理员 JWT 寿命
function isTokenExpired(token) {
  if (!token) return true
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    const payload = JSON.parse(jsonPayload)
    const now = Math.floor(Date.now() / 1000)
    return payload.exp < now
  } catch (e) {
    return true
  }
}

export const useAuthStore = defineStore('auth', () => {
  // 缓存管理员的专属身份信息
  const token = ref(localStorage.getItem('admin_token') || '')
  const username = ref(localStorage.getItem('admin_username') || '')

  // 静态自检：若过期则瞬间注销
  if (token.value && isTokenExpired(token.value)) {
    token.value = ''
    username.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
  }

  // 💡 安全约束：不仅要求有 Token，且必须要求登录用户名必须为 'admin' 
  const isLoggedIn = computed(() => !!token.value && username.value === 'admin')

  function setLogin(newToken, newUser) {
    if (newUser !== 'admin') {
      alert('您不是系统管理员，无权登录后台')
      return false
    }
    token.value = newToken
    username.value = newUser
    localStorage.setItem('admin_token', newToken)
    localStorage.setItem('admin_username', newUser)
    return true
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
  }

  return { token, username, isLoggedIn, setLogin, logout }
})