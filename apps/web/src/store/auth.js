// src/store/auth.js
// 用户端登录态：Token 与基础资料持久化在 localStorage。
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { isTokenExpired } from '@drive/shared'

const STORAGE_KEYS = {
  token: 'drive_token',
  username: 'drive_username',
  nickname: 'drive_nickname',
  avatar: 'drive_avatar',
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(STORAGE_KEYS.token) || '')
  const username = ref(localStorage.getItem(STORAGE_KEYS.username) || '')
  const nickname = ref(localStorage.getItem(STORAGE_KEYS.nickname) || '')
  const avatar = ref(localStorage.getItem(STORAGE_KEYS.avatar) || '👤')

  if (token.value && isTokenExpired(token.value)) {
    logout()
    console.warn('🔐 安全自检：本地登录凭证已过期，已被安全擦除')
  }

  const isLoggedIn = computed(() => !!token.value)

  function setLogin(newToken, newUser, newNickname = '', newAvatar = '👤') {
    token.value = newToken
    username.value = newUser
    nickname.value = newNickname || newUser
    avatar.value = newAvatar || '👤'

    localStorage.setItem(STORAGE_KEYS.token, newToken)
    localStorage.setItem(STORAGE_KEYS.username, newUser)
    localStorage.setItem(STORAGE_KEYS.nickname, nickname.value)
    localStorage.setItem(STORAGE_KEYS.avatar, avatar.value)
  }

  function updateProfileState(newNickname, newAvatar) {
    nickname.value = newNickname
    avatar.value = newAvatar
    localStorage.setItem(STORAGE_KEYS.nickname, newNickname)
    localStorage.setItem(STORAGE_KEYS.avatar, newAvatar)
  }

  function logout() {
    token.value = ''
    username.value = ''
    nickname.value = ''
    avatar.value = '👤'
    Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key))
  }

  return { token, username, nickname, avatar, isLoggedIn, setLogin, updateProfileState, logout }
})
