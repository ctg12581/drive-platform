// src/utils/api.js
// 用户端 API 配置：baseURL / WebSocket 地址在这里集中维护，
// 通用请求逻辑（Token、FormData、401 拦截）复用 @drive/shared。
import { createApiFetch } from '@drive/shared'
import { useAuthStore } from '../store/auth'
import router from '../router'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:3000'
export const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://127.0.0.1:3000'

/**
 * 全站统一请求工具：自动携带 Token、处理 FormData，401 时清理登录态并跳转登录页。
 */
export const apiFetch = createApiFetch({
  baseURL: API_BASE,
  getToken: () => useAuthStore().token,
  onUnauthorized: () => {
    const authStore = useAuthStore()
    authStore.logout()
    if (router.currentRoute.value.path !== '/auth') {
      router.push('/auth')
    }
  },
})
