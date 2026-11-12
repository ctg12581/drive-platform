// src/store/auth.js
// 管理后台登录态：仅允许 username === 'admin' 的管理员登录。
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { isTokenExpired } from '@drive/shared'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const username = ref(localStorage.getItem('admin_username') || '')

  if (token.value && isTokenExpired(token.value)) {
    token.value = ''
    username.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
  }

  const isLoggedIn = computed(() => !!token.value && username.value === 'admin')

  function setLogin(newToken, newUser) {
    if (newUser !== 'admin') return false
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
