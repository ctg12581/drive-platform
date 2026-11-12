// src/utils/api.js
// 管理后台 API 配置：401 时清理管理员登录态并跳转 /login。
import { createApiFetch } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import router from '../router'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:3000'

export const apiFetch = createApiFetch({
  baseURL: API_BASE,
  getToken: () => useAuthStore().token,
  onUnauthorized: () => {
    const authStore = useAuthStore()
    authStore.logout()
    if (router.currentRoute.value.path !== '/login') {
      router.push('/login')
    }
  },
})
